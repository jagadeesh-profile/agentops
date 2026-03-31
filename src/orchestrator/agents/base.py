from __future__ import annotations

import time
from abc import ABC, abstractmethod

from orchestrator.memory.store import PersistentMemoryStore
from orchestrator.models import AgentArtifact
from orchestrator.tools.registry import ToolRegistry


class BaseAgent(ABC):
    def __init__(self, name: str, memory: PersistentMemoryStore, tools: ToolRegistry) -> None:
        self.name = name
        self.memory = memory
        self.tools = tools

    @abstractmethod
    def run(self, session_id: str, topic: str, prior_output: str | None = None) -> AgentArtifact:
        ...

    def _artifact(self, content: str, sources: list[str], start: float) -> AgentArtifact:
        return AgentArtifact(
            agent_name=self.name,
            content=content,
            sources=sources,
            latency_ms=int((time.perf_counter() - start) * 1000),
        )
