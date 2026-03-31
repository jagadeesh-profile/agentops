from __future__ import annotations

import time

from orchestrator.agents.base import BaseAgent


class RetrievalAgent(BaseAgent):
    def run(self, session_id: str, topic: str, prior_output: str | None = None):
        start = time.perf_counter()
        web = self.tools.run("web_search", topic)
        vec = self.tools.run("vector_retrieval", topic)
        content = f"Retrieved evidence:\n- {web}\n- {vec}"
        self.memory.upsert(session_id, self.name, "last_retrieval", content)
        return self._artifact(content=content, sources=["web_search", "vector_retrieval"], start=start)
