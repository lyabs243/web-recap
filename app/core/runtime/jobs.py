import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4


@dataclass
class JobRecord:
    job_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completed: bool = False
    history: list[dict[str, Any]] = field(default_factory=list)
    condition: asyncio.Condition = field(default_factory=asyncio.Condition)


class InMemoryJobStore:
    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = timedelta(seconds=ttl_seconds)
        self._jobs: dict[str, JobRecord] = {}
        self._lock = asyncio.Lock()

    async def create_job(self) -> str:
        job_id = uuid4().hex
        async with self._lock:
            self._jobs[job_id] = JobRecord(job_id=job_id)
        return job_id

    async def get_job(self, job_id: str) -> JobRecord | None:
        await self._expire_jobs()
        async with self._lock:
            return self._jobs.get(job_id)

    async def append_event(self, job_id: str, event: dict[str, Any]) -> None:
        record = await self.get_job(job_id)
        if record is None:
            return

        async with record.condition:
            record.history.append(event)
            if event.get("type") in {"completed", "failed"}:
                record.completed = True
            record.condition.notify_all()

    async def wait_for_events(
        self,
        job_id: str,
        cursor: int,
        timeout: float = 30.0,
    ) -> tuple[list[dict[str, Any]], int, bool]:
        record = await self.get_job(job_id)
        if record is None:
            raise KeyError(job_id)

        async with record.condition:
            if cursor >= len(record.history) and not record.completed:
                await asyncio.wait_for(record.condition.wait(), timeout=timeout)

            events = record.history[cursor:]
            next_cursor = len(record.history)
            return events, next_cursor, record.completed

    async def _expire_jobs(self) -> None:
        now = datetime.now(UTC)
        async with self._lock:
            expired = [
                job_id
                for job_id, record in self._jobs.items()
                if record.completed and now - record.created_at > self._ttl
            ]
            for job_id in expired:
                del self._jobs[job_id]