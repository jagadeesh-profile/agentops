from __future__ import annotations

import time

from orchestrator.agents.base import BaseAgent


class SynthesisAgent(BaseAgent):
    def run(self, session_id: str, topic: str, prior_output: str | None = None):
        start = time.perf_counter()
        prior = prior_output or self.memory.get(session_id, "retrieval", "last_retrieval") or "No evidence"
        summary = (
            f"Synthesis for '{topic}':\n"
            f"{prior}\n"
            "Key insight: integrated findings indicate practical automation gains with measurable latency targets."
        )
        self.memory.upsert(session_id, self.name, "last_summary", summary)
        return self._artifact(content=summary, sources=["retrieval_artifact"], start=start)
