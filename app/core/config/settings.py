from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = Field(default="development", alias="APP_ENV")
    app_host: str = Field(default="127.0.0.1", alias="APP_HOST")
    app_port: int = Field(default=8000, alias="APP_PORT")
    frontend_dir: Path = Field(default=Path("frontend"), alias="FRONTEND_DIR")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    brave_api_key: str = Field(default="", alias="BRAVE_API_KEY")
    headless_browser: bool = Field(default=False, alias="HEADLESS_BROWSER")
    max_articles: int = Field(default=5, alias="MAX_ARTICLES")
    job_ttl_seconds: int = Field(default=1800, alias="JOB_TTL_SECONDS")

    # LangSmith tracing
    langsmith_tracing: str = Field(default="false", alias="LANGSMITH_TRACING")
    langsmith_endpoint: str = Field(default="https://api.smith.langchain.com", alias="LANGSMITH_ENDPOINT")
    langsmith_api_key: str = Field(default="", alias="LANGSMITH_API_KEY")
    langsmith_project: str = Field(default="", alias="LANGSMITH_PROJECT")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()