from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from orchestrator.agents import CritiqueAgent, RetrievalAgent, SynthesisAgent
from orchestrator.config import settings
from orchestrator.memory.store import PersistentMemoryStore
from orchestrator.messaging import AutoGenMessageBus
from orchestrator.models import Job, ResearchRequest
from orchestrator.queue import AsyncJobQueue
from orchestrator.tools.code_executor import CodeExecutionTool
from orchestrator.tools.registry import ToolRegistry
from orchestrator.tools.vector_retrieval import VectorRetrievalTool
from orchestrator.tools.web_search import WebSearchTool
from orchestrator.workflow import MultiAgentWorkflow


def build_app() -> FastAPI:
    memory = PersistentMemoryStore(settings.memory_db_path)
    tools = ToolRegistry()
    tools.register(WebSearchTool(fake_results=settings.enable_fake_tool_results))
    tools.register(VectorRetrievalTool(fake_results=settings.enable_fake_tool_results))
    tools.register(CodeExecutionTool())

    bus = AutoGenMessageBus()
    retrieval = RetrievalAgent(name="retrieval", memory=memory, tools=tools)
    synthesis = SynthesisAgent(name="synthesis", memory=memory, tools=tools)
    critique = CritiqueAgent(name="critique", memory=memory, tools=tools)

    workflow = MultiAgentWorkflow(
        retrieval_agent=retrieval,
        synthesis_agent=synthesis,
        critique_agent=critique,
        message_bus=bus,
    )

    queue = AsyncJobQueue(workflow=workflow, max_concurrent_jobs=settings.max_concurrent_jobs)

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        await queue.start()
        try:
            yield
        finally:
            await queue.stop()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"service": settings.app_name, "status": "running", "docs": "/docs"}

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/jobs", response_model=Job)
    async def submit_job(request: ResearchRequest) -> Job:
        return await queue.submit(request)

    @app.get("/jobs/{job_id}", response_model=Job)
    async def get_job(job_id: str) -> Job:
        job = await queue.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job

    return app


app = build_app()
