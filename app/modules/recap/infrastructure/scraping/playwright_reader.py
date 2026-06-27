import asyncio

from playwright.sync_api import sync_playwright

from app.core.config.settings import Settings
from app.modules.recap.application.services.text_utils import normalize_text
from app.modules.recap.domain.entities.recap import SearchReference, SourceArticle


class PlaywrightArticleReader:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    async def read_article(self, reference: SearchReference) -> SourceArticle:
        return await asyncio.to_thread(self._read_article_sync, reference)

    def _read_article_sync(self, reference: SearchReference) -> SourceArticle:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=self._settings.headless_browser)
            page = browser.new_page()
            page.goto(reference.url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(1500)

            title = page.title()
            extracted_text = self._extract_main_text(page)
            browser.close()

        return SourceArticle(
            url=reference.url,
            search_title=reference.title,
            extracted_title=normalize_text(title or reference.title),
            cleaned_text=extracted_text,
            snippet=reference.snippet,
            favicon_url=reference.favicon_url,
            source=reference.source,
        )

    def _extract_main_text(self, page) -> str:
        selectors = ["article", "main", "[role='main']", "body"]
        best_text = ""
        for selector in selectors:
            locator = page.locator(selector).first
            if locator.count() == 0:
                continue
            text = normalize_text(locator.inner_text())
            if len(text) > len(best_text):
                best_text = text
        return best_text