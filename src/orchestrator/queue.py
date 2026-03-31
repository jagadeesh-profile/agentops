from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

from orchestrator.models import Job, JobStatus, ResearchRequest
from orchestrator.workflow import MultiAgentWorkflow


class AsyncJobQueue:
    def __init__(self, workflow: MultiAgentWorkflow, max_concurrent_jobs: int = 4) -> None:
        self.workflow = workflow
        self.max_concurrent_jobs = max_concurrent_jobs
        self._queue: asyncio.Queue[str] = asyncio.Queue()
        self._jobs: dict[str, Job] = {}
        self._lock = asyncio.Lock()
        self._workers: list[asyncio.Task] = []
        self._running = False

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._workers = [asyncio.create_task(self._worker_loop()) for _ in range(self.max_concurrent_jobs)]

    async def stop(self) -> None:
        self._running = False
        for task in self._workers:
            task.cancel()
        await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()

    async def submit(self, request: ResearchRequest) -> Job:
        async with self._lock:
            job_id = str(uuid.uuid4())
            job = Job(id=job_id, request=request)
            self._jobs[job_id] = job
            await self._queue.put(job_id)
            return job

    async def get(self, job_id: str) -> Job | None:
        async with self._lock:
            return self._jobs.get(job_id)

    async def _worker_loop(self) -> None:
        while True:
            job_id = await self._queue.get()
            await self._execute_job(job_id)
            self._queue.task_done()

    async def _execute_job(self, job_id: str) -> None:
        async with self._lock:
            job = self._jobs[job_id]
            job.status = JobStatus.running
            job.updated_at = datetime.now(timezone.utc)

        try:
            result = await asyncio.to_thread(self.workflow.run, job.request)
            async with self._lock:
                job.result = result
                job.status = JobStatus.completed
                job.updated_at = datetime.now(timezone.utc)
        except Exception as exc:
            async with self._lock:
                job.status = JobStatus.failed
                job.error = str(exc)
                job.updated_at = datetime.now(timezone.utc)
