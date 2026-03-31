from __future__ import annotations

import time

from orchestrator.agents.base import BaseAgent


class CritiqueAgent(BaseAgent):
    def run(self, session_id: str, topic: str, prior_output: str | None = None):
        start = time.perf_counter()
        draft = prior_output or self.memory.get(session_id, "synthesis", "last_summary") or "No draft"
        critique = (
            f"Critique for '{topic}':\n"
            "- Validate source credibility and recency.\n"
            "- Cross-check contradictory signals before final recommendation.\n"
            f"- Reviewed draft length: {len(draft)} characters."
        )
        self.memory.upsert(session_id, self.name, "last_critique", critique)
        return self._artifact(content=critique, sources=["synthesis_artifact"], start=start)
