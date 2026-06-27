import asyncio

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.core.config.settings import Settings, get_settings
from app.core.runtime.jobs import InMemoryJobStore
from app.modules.recap.application.dto.schemas import JobAcceptedResponse, RecapSubmitRequest
from app.modules.recap.application.services.workflow import RecapWorkflowService
from app.modules.recap.infrastructure.llm.openai_factory import OpenAIModelFactory
from app.modules.recap.infrastructure.scraping.playwright_reader import PlaywrightArticleReader
from app.modules.recap.infrastructure.search.brave_client import BraveSearchClient


router = APIRouter(prefix="/api/recaps", tags=["recaps"])
_job_store: InMemoryJobStore | None = None
_workflow_service: RecapWorkflowService | None = None


def get_job_store(settings: Settings = Depends(get_settings)) -> InMemoryJobStore:
    global _job_store
    if _job_store is None:
        _job_store = InMemoryJobStore(ttl_seconds=settings.job_ttl_seconds)
    return _job_store


def get_workflow_service(
    settings: Settings = Depends(get_settings),
    jobs: InMemoryJobStore = Depends(get_job_store),
) -> RecapWorkflowService:
    global _workflow_service
    if _workflow_service is None:
        _workflow_service = RecapWorkflowService(
            settings=settings,
            jobs=jobs,
            search_client=BraveSearchClient(settings),
            article_reader=PlaywrightArticleReader(settings),
            model_factory=OpenAIModelFactory(settings),
        )
    return _workflow_service


@router.post("", response_model=JobAcceptedResponse)
async def submit_recap(
    request: RecapSubmitRequest,
    jobs: InMemoryJobStore = Depends(get_job_store),
    workflow: RecapWorkflowService = Depends(get_workflow_service),
) -> JobAcceptedResponse:
    job_id = await jobs.create_job()
    asyncio.create_task(workflow.run(job_id, request))
    return JobAcceptedResponse(job_id=job_id)


@router.websocket("/{job_id}/stream")
async def stream_recap(job_id: str, websocket: WebSocket) -> None:
    await websocket.accept()
    jobs = get_job_store(get_settings())
    job = await jobs.get_job(job_id)
    if job is None:
        await websocket.send_json({"type": "failed", "stage": "stream", "message": "Unknown job id"})
        await websocket.close(code=1008)
        return

    cursor = 0
    try:
        while True:
            try:
                events, cursor, completed = await jobs.wait_for_events(job_id, cursor)
            except TimeoutError:
                await websocket.send_json(
                    {"type": "progress", "stage": "stream", "message": "Waiting for next event..."}
                )
                continue

            for event in events:
                await websocket.send_json(event)

            if completed:
                break
    except WebSocketDisconnect:
        return
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc
    finally:
        if websocket.application_state is not WebSocketState.DISCONNECTED:
            await websocket.close()