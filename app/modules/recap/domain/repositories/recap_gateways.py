from typing import Protocol

from app.modules.recap.domain.entities.recap import LanguageCode, SearchReference, SourceArticle


class NewsSearchGateway(Protocol):
    async def search_news(self, topic: str, language: LanguageCode, max_results: int) -> list[SearchReference]:
        ...


class ArticleReaderGateway(Protocol):
    async def read_article(self, reference: SearchReference) -> SourceArticle:
        ...