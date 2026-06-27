from langchain_core.prompts import ChatPromptTemplate

from app.modules.recap.application.services.chains.models import ArticleOutlineOutput, SourcePlanOutput
from app.modules.recap.application.services.prompts.outline import (
    ARTICLE_OUTLINE_SYSTEM_PROMPT,
    ARTICLE_OUTLINE_USER_PROMPT,
    SOURCE_PLAN_SYSTEM_PROMPT,
    SOURCE_PLAN_USER_PROMPT,
)


def build_source_plan_chain(model):
    prompt = ChatPromptTemplate.from_messages(
        [("system", SOURCE_PLAN_SYSTEM_PROMPT), ("human", SOURCE_PLAN_USER_PROMPT)]
    )
    return prompt | model.with_structured_output(SourcePlanOutput)


def build_article_outline_chain(model):
    prompt = ChatPromptTemplate.from_messages(
        [("system", ARTICLE_OUTLINE_SYSTEM_PROMPT), ("human", ARTICLE_OUTLINE_USER_PROMPT)]
    )
    return prompt | model.with_structured_output(ArticleOutlineOutput)