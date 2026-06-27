from urllib.parse import urlparse

import httpx

from app.core.config.settings import Settings
from app.modules.recap.domain.entities.recap import LanguageCode, SearchReference


class BraveSearchClient:
    BASE_URL = "https://api.search.brave.com/res/v1/news/search"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def search_news(self, topic: str, language: LanguageCode, max_results: int) -> list[SearchReference]:
        if not self._settings.brave_api_key:
            raise RuntimeError("BRAVE_API_KEY is not configured")

        primary = await self._search(topic, language, max_results)
        if language != "en" and len(primary) < max_results:
            fallback = await self._search(topic, "en", max_results)
            primary_urls = {item.url for item in primary}
            primary.extend(item for item in fallback if item.url not in primary_urls)
        return primary[:max_results]

    async def _search(self, topic: str, language: LanguageCode, max_results: int) -> list[SearchReference]:
        params = {"q": topic, "count": max_results, "search_lang": language, "spellcheck": 1}
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self._settings.brave_api_key,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.BASE_URL, params=params, headers=headers)
            response.raise_for_status()

        payload = response.json()
        results = payload.get("results", [])
        return [self._map_result(item) for item in results]

    def _map_result(self, item: dict) -> SearchReference:
        url = item.get("url", "")
        meta_url = item.get("meta_url") or {}
        profile = item.get("profile") or {}
        source = meta_url.get("hostname") or profile.get("name") or urlparse(url).netloc
        favicon_url = profile.get("img") or f"https://www.google.com/s2/favicons?sz=64&domain_url={url}"
        return SearchReference(
            title=item.get("title", url),
            url=url,
            snippet=item.get("description", ""),
            favicon_url=favicon_url,
            source=source,
        )