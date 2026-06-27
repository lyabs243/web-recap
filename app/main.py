from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env as early as possible for LangChain/LangSmith
load_dotenv()

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config.settings import get_settings
from app.modules.recap.presentation.routes.recap import router as recap_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Web Recap", version="0.1.0")
    app.include_router(recap_router)

    frontend_dir = Path(settings.frontend_dir)
    if frontend_dir.exists():
        app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")

        @app.get("/", include_in_schema=False)
        async def index() -> FileResponse:
            return FileResponse(frontend_dir / "index.html")

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()