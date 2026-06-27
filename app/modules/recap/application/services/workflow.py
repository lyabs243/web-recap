import asyncio
from datetime import datetime
from typing import Any, TypedDict

from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, START, StateGraph

from app.core.config.settings import Settings
from app.core.runtime.jobs import InMemoryJobStore
from app.modules.recap.application.dto.schemas import ProgressEventResponse, RecapSubmitRequest
from app.modules.recap.application.services.chains.clean_chain import build_clean_chain
from app.modules.recap.application.services.chains.outline_chain import (
    build_article_outline_chain,
    build_source_plan_chain,
)
from app.modules.recap.application.services.chains.query_chain import build_query_chain
from app.modules.recap.application.services.prompts.section import (
    SECTION_WRITER_SYSTEM_PROMPT,
    SECTION_WRITER_USER_PROMPT,
)
from app.modules.recap.application.services.text_utils import language_name, trim_to_chars
from app.modules.recap.domain.entities.recap import (
    GeneratedSection,
    OutlineSection,
    RecapDocument,
    RecapOutline,
    RecapRequest,
    SearchReference,
    SourceArticle,
    SourcePlan,
)
from app.modules.recap.infrastructure.llm.openai_factory import OpenAIModelFactory
from app.modules.recap.infrastructure.scraping.playwright_reader import PlaywrightArticleReader
from app.modules.recap.infrastructure.search.brave_client import BraveSearchClient


class RecapState(TypedDict, total=False):
    job_id: str
    request: RecapRequest
    search_query: str
    references: list[SearchReference]
    sources: list[SourceArticle]
    source_plans: list[SourcePlan]
    outline: RecapOutline
    sections: list[GeneratedSection]
    result: RecapDocument


class RecapWorkflowService:
    def __init__(
        self,
        settings: Settings,
        jobs: InMemoryJobStore,
        search_client: BraveSearchClient,
        article_reader: PlaywrightArticleReader,
        model_factory: OpenAIModelFactory,
    ) -> None:
        self._settings = settings
        self._jobs = jobs
        self._search_client = search_client
        self._article_reader = article_reader
        self._model_factory = model_factory
        self._query_chain = build_query_chain(model_factory.nano())
        self._clean_chain = build_clean_chain(model_factory.nano())
        self._source_plan_chain = build_source_plan_chain(model_factory.nano())
        self._outline_chain = build_article_outline_chain(model_factory.mini())
        self._section_prompt = ChatPromptTemplate.from_messages(
            [("system", SECTION_WRITER_SYSTEM_PROMPT), ("human", SECTION_WRITER_USER_PROMPT)]
        )
        self._section_chain = self._section_prompt | model_factory.nano()
        self._graph = self._build_graph()

    async def run(self, job_id: str, request_data: RecapSubmitRequest) -> None:
        try:
            initial_state: RecapState = {
                "job_id": job_id,
                "request": RecapRequest(
                    topic=request_data.topic,
                    language=request_data.language,
                    max_results=self._settings.max_articles,
                ),
            }
            await self._graph.ainvoke(initial_state)
        except Exception as exc:
            await self._jobs.append_event(
                job_id,
                ProgressEventResponse(
                    type="failed",
                    stage="workflow",
                    message=str(exc),
                    payload={"error_type": type(exc).__name__},
                ).model_dump(),
            )

    def _build_graph(self):
        graph = StateGraph(RecapState)
        graph.add_node("generate_query", self._generate_query)
        graph.add_node("search_news", self._search_news)
        graph.add_node("fetch_articles", self._fetch_articles)
        graph.add_node("plan_sources", self._plan_sources)
        graph.add_node("plan_article", self._plan_article)
        graph.add_node("write_sections", self._write_sections)
        graph.add_node("compose_result", self._compose_result)
        graph.add_edge(START, "generate_query")
        graph.add_edge("generate_query", "search_news")
        graph.add_edge("search_news", "fetch_articles")
        graph.add_edge("fetch_articles", "plan_sources")
        graph.add_edge("plan_sources", "plan_article")
        graph.add_edge("plan_article", "write_sections")
        graph.add_edge("write_sections", "compose_result")
        graph.add_edge("compose_result", END)
        return graph.compile()

    async def _generate_query(self, state: RecapState) -> RecapState:
        request = state["request"]
        await self._progress(state, "query", "Generating a news-focused search query.")
        current_date = datetime.now().strftime("%Y-%m-%d")
        result = await self._query_chain.ainvoke(
            {
                "topic": request.topic,
                "language": language_name(request.language),
                "current_date": current_date,
            }
        )
        return {"search_query": result.query}

    async def _search_news(self, state: RecapState) -> RecapState:
        request = state["request"]
        await self._progress(state, "search", "Searching Brave News.")
        references = await self._search_client.search_news(
            state["search_query"], request.language, request.max_results
        )
        if not references:
            raise RuntimeError("No news results were found for this topic")
        await self._progress(
            state,
            "search",
            f"Collected {len(references)} news links.",
            payload={"links": [reference.url for reference in references]},
        )
        return {"references": references}

    async def _fetch_articles(self, state: RecapState) -> RecapState:
        await self._progress(state, "scrape", "Reading and cleaning article pages.")
        semaphore = asyncio.Semaphore(2)
        request = state["request"]

        async def process_reference(reference: SearchReference) -> SourceArticle:
            async with semaphore:
                await self._progress(
                    state,
                    "scrape",
                    f"Opening {reference.source} in Playwright.",
                    payload={"url": reference.url},
                )
                article = await self._article_reader.read_article(reference)
                cleaned = await self._clean_chain.ainvoke(
                    {"title": article.extracted_title, "url": article.url, "text": article.cleaned_text}
                )
                await self._progress(
                    state,
                    "clean",
                    f"Cleaned source text for {reference.source}.",
                    payload={"url": reference.url},
                )
                return SourceArticle(
                    url=article.url,
                    search_title=article.search_title,
                    extracted_title=cleaned.title,
                    cleaned_text=trim_to_chars(cleaned.cleaned_text, 3000),
                    snippet=article.snippet,
                    favicon_url=article.favicon_url,
                    source=article.source,
                )

        sources = await asyncio.gather(*(process_reference(reference) for reference in state["references"]))
        if not sources:
            raise RuntimeError("Unable to read any article content")
        await self._progress(state, "clean", "Prepared article bodies for planning.")
        return {"sources": sources}

    async def _plan_sources(self, state: RecapState) -> RecapState:
        request = state["request"]
        plans: list[SourcePlan] = []
        for source in state["sources"]:
            await self._progress(
                state,
                "source-plan",
                f"Extracting article angle from {source.source}.",
                payload={"url": source.url},
            )
            plan = await self._source_plan_chain.ainvoke(
                {
                    "topic": request.topic,
                    "language": language_name(request.language),
                    "title": source.extracted_title,
                    "text": source.cleaned_text,
                }
            )
            plans.append(
                SourcePlan(article_title=plan.article_title, angle=plan.angle, key_points=plan.key_points)
            )
        return {"source_plans": plans}

    async def _plan_article(self, state: RecapState) -> RecapState:
        request = state["request"]
        await self._progress(state, "outline", "Creating the recap outline.")
        evidence = "\n\n".join(
            f"Title: {plan.article_title}\nAngle: {plan.angle}\nPoints: {'; '.join(plan.key_points)}"
            for plan in state["source_plans"]
        )
        outline = await self._outline_chain.ainvoke(
            {
                "topic": request.topic,
                "language": language_name(request.language),
                "evidence": evidence,
            }
        )
        return {
            "outline": RecapOutline(
                title=outline.title,
                intro=outline.intro,
                sections=[
                    OutlineSection(heading=section.heading, purpose=section.purpose)
                    for section in outline.sections
                ],
                conclusion=outline.conclusion,
            )
        }

    async def _write_sections(self, state: RecapState) -> RecapState:
        request = state["request"]
        outline = state["outline"]
        evidence = "\n\n".join(
            f"Source: {source.source}\nTitle: {plan.article_title}\nAngle: {plan.angle}\nPoints: {'; '.join(plan.key_points)}"
            for source, plan in zip(state["sources"], state["source_plans"], strict=True)
        )
        sections: list[GeneratedSection] = []
        for section in outline.sections:
            await self._progress(state, "write", f"Writing section: {section.heading}")
            message = await self._section_chain.ainvoke(
                {
                    "language": language_name(request.language),
                    "article_title": outline.title,
                    "heading": section.heading,
                    "purpose": section.purpose,
                    "intro": outline.intro,
                    "conclusion": outline.conclusion,
                    "evidence": evidence,
                }
            )
            sections.append(GeneratedSection(heading=section.heading, markdown=message.content.strip()))
        return {"sections": sections}

    async def _compose_result(self, state: RecapState) -> RecapState:
        outline = state["outline"]
        body = [f"# {outline.title}", outline.intro]
        for section in state["sections"]:
            body.append(section.markdown)
        body.append(f"## Conclusion\n\n{outline.conclusion}")
        markdown = "\n\n".join(body).strip()
        result = RecapDocument(title=outline.title, markdown=markdown, references=state["references"])
        await self._jobs.append_event(
            state["job_id"],
            {
                "type": "completed",
                "stage": "done",
                "message": "Recap article ready.",
                "payload": {
                    "result": {
                        "title": result.title,
                        "markdown": result.markdown,
                        "references": [
                            {
                                "title": reference.title,
                                "url": reference.url,
                                "snippet": reference.snippet,
                                "favicon_url": reference.favicon_url,
                                "source": reference.source,
                            }
                            for reference in result.references
                        ],
                    }
                },
            },
        )
        return {"result": result}

    async def _progress(
        self,
        state: RecapState,
        stage: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        await self._jobs.append_event(
            state["job_id"],
            ProgressEventResponse(type="progress", stage=stage, message=message, payload=payload).model_dump(),
        )