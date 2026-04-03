"""
Tests that directly validate the business claims:
  - Sub-3s agent handoff latency across the pipeline
  - Zero state collision across concurrent sessions
  - Async job queue submit → poll → complete end-to-end
"""
from __future__ import annotations

import asyncio
import threading

import pytest

from orchestrator.agents import CritiqueAgent, RetrievalAgent, SynthesisAgent
from orchestrator.memory.store import PersistentMemoryStore
from orchestrator.messaging import AutoGenMessageBus
from orchestrator.models import ResearchRequest
from orchestrator.queue import AsyncJobQueue
from orchestrator.tools.code_executor import CodeExecutionTool
from orchestrator.tools.registry import ToolRegistry
from orchestrator.tools.vector_retrieval import VectorRetrievalTool
from orchestrator.tools.web_search import WebSearchTool
from orchestrator.workflow import MultiAgentWorkflow


def _make_workflow(tmp_path, db_name: str = "memory.db") -> MultiAgentWorkflow:
    memory = PersistentMemoryStore(str(tmp_path / db_name))
    tools = ToolRegistry()
    tools.register(WebSearchTool(fake_results=True))
    tools.register(VectorRetrievalTool(fake_results=True))
    tools.register(CodeExecutionTool())
    return MultiAgentWorkflow(
        retrieval_agent=RetrievalAgent("retrieval", memory, tools),
        synthesis_agent=SynthesisAgent("synthesis", memory, tools),
        critique_agent=CritiqueAgent("critique", memory, tools),
        message_bus=AutoGenMessageBus(),
    )


# ---------------------------------------------------------------------------
# Claim: sub-3s agent handoff latency
# ---------------------------------------------------------------------------

def test_handoff_latencies_are_under_3_seconds(tmp_path):
    workflow = _make_workflow(tmp_path)
    result = workflow.run(ResearchRequest(session_id="lat-1", topic="Latency test"))

    assert len(result.handoff_latencies_ms) == 2, (
        "Expected 2 handoffs: retrieval→synthesis and synthesis→critique"
    )
    for i, lat in enumerate(result.handoff_latencies_ms):
        assert lat < 3000, (
            f"Handoff {i} latency {lat}ms exceeds 3 000ms SLA"
        )


# ---------------------------------------------------------------------------
# Claim: zero state collision across concurrent sessions
# ---------------------------------------------------------------------------

def test_concurrent_sessions_no_state_collision(tmp_path):
    """Run 5 sessions in parallel threads; verify each session's memory is
    isolated — no session reads another session's retrieval output."""
    workflow = _make_workflow(tmp_path)
    topics = [f"Topic {i}" for i in range(5)]
    results: dict[int, object] = {}
    errors: list[Exception] = []

    def run_session(idx: int) -> None:
        try:
            req = ResearchRequest(session_id=f"concurrent-{idx}", topic=topics[idx])
            results[idx] = workflow.run(req)
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=run_session, args=(i,)) for i in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"Exceptions in concurrent sessions: {errors}"
    assert len(results) == 5

    # Each session result must contain only its own topic, not any other topic's text
    for idx, result in results.items():
        own_topic = topics[idx]
        for other_idx, other_topic in enumerate(topics):
            if other_idx == idx:
                continue
            assert other_topic not in result.summary, (
                f"Session {idx} summary contains topic from session {other_idx} — state collision detected"
            )


# ---------------------------------------------------------------------------
# Claim: async job queue submit → poll → complete
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_async_job_queue_end_to_end(tmp_path):
    workflow = _make_workflow(tmp_path)
    queue = AsyncJobQueue(workflow=workflow, max_concurrent_jobs=4)

    await queue.start()
    try:
        job = await queue.submit(
            ResearchRequest(session_id="queue-e2e-1", topic="Async queue validation")
        )
        assert job.status.value == "queued"

        # Poll until completed (max 10s)
        for _ in range(100):
            polled = await queue.get(job.id)
            if polled.status.value in ("completed", "failed"):
                break
            await asyncio.sleep(0.1)

        assert polled.status.value == "completed", f"Job ended with status: {polled.status}"
        assert polled.result is not None
        assert polled.result.session_id == "queue-e2e-1"
        assert len(polled.result.artifacts) == 3
    finally:
        await queue.stop()
