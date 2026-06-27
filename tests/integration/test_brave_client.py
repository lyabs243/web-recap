from app.core.config.settings import Settings
from app.modules.recap.infrastructure.search.brave_client import BraveSearchClient


class FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self._payload


class FakeAsyncClient:
    def __init__(self, responses: list[dict]) -> None:
        self._responses = responses
        self.calls: list[dict] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url: str, params: dict, headers: dict) -> FakeResponse:
        self.calls.append({"url": url, "params": params, "headers": headers})
        return FakeResponse(self._responses.pop(0))


async def test_brave_client_falls_back_to_english(monkeypatch) -> None:
    responses = [
        {
            "results": [
                {
                    "title": "Titre FR",
                    "url": "https://example.fr/news",
                    "description": "Resume FR",
                    "meta_url": {"hostname": "example.fr"},
                }
            ]
        },
        {
            "results": [
                {
                    "title": "English Title",
                    "url": "https://example.com/news",
                    "description": "English summary",
                    "meta_url": {"hostname": "example.com"},
                }
            ]
        },
    ]
    fake_client = FakeAsyncClient(responses)

    def fake_async_client(*args, **kwargs):
        return fake_client

    monkeypatch.setattr("app.modules.recap.infrastructure.search.brave_client.httpx.AsyncClient", fake_async_client)

    settings = Settings(BRAVE_API_KEY="token")
    client = BraveSearchClient(settings)

    results = await client.search_news("topic", "fr", 2)

    assert [item.url for item in results] == ["https://example.fr/news", "https://example.com/news"]
    assert fake_client.calls[0]["params"]["search_lang"] == "fr"
    assert fake_client.calls[1]["params"]["search_lang"] == "en"