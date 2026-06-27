import asyncio

from fastapi.testclient import TestClient

from app.core.runtime.jobs import InMemoryJobStore
from app.main import create_app
from app.modules.recap.presentation.routes import recap as recap_routes


class FakeWorkflowService:
    def __init__(self, job_store: InMemoryJobStore) -> None:
        self._job_store = job_store

    async def run(self, job_id: str, request_data) -> None:
        await self._job_store.append_event(
            job_id,
            {
                "type": "progress",
                "stage": "query",
                "message": f"Started for {request_data.topic}",
                "timestamp": "2026-06-27T12:00:00+00:00",
                "payload": None,
            },
        )
        await asyncio.sleep(0)
        await self._job_store.append_event(
            job_id,
            {
                "type": "completed",
                "stage": "done",
                "message": "Recap article ready.",
                "timestamp": "2026-06-27T12:00:01+00:00",
                "payload": {
                    "result": {
                        "title": "Test recap",
                        "markdown": "# Test recap\n\n## Summary\nHello",
                        "references": [
                            {
                                "title": "Ref",
                                "url": "https://example.com",
                                "snippet": "Snippet",
                                "favicon_url": "https://example.com/favicon.ico",
                                "source": "example.com",
                            }
                        ],
                    }
                },
            },
        )


def test_submit_and_stream_recap_job() -> None:
    recap_routes._job_store = InMemoryJobStore(ttl_seconds=1800)
    recap_routes._workflow_service = FakeWorkflowService(recap_routes._job_store)
    client = TestClient(create_app())

    response = client.post("/api/recaps", json={"topic": "ECB policy", "language": "en"})
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    with client.websocket_connect(f"/api/recaps/{job_id}/stream") as websocket:
        first_event = websocket.receive_json()
        second_event = websocket.receive_json()

    assert first_event["type"] == "progress"
    assert second_event["type"] == "completed"
    assert second_event["payload"]["result"]["title"] == "Test recap"