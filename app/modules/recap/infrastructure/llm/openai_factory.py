from langchain_openai import ChatOpenAI

from app.core.config.settings import Settings


class OpenAIModelFactory:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def mini(self) -> ChatOpenAI:
        return ChatOpenAI(model="gpt-4o-mini", api_key=self._settings.openai_api_key, temperature=0.2)

    def nano(self) -> ChatOpenAI:
        return ChatOpenAI(model="gpt-4.1-nano", api_key=self._settings.openai_api_key, temperature=0.1)