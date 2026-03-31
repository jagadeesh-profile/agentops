from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from orchestrator.models import AgentMessage


class AutoGenMessageBus:
    """Lightweight in-process message bus that mimics AutoGen-style handoffs."""

    def __init__(self) -> None:
        self._mailboxes: dict[str, list[AgentMessage]] = defaultdict(list)
        self._handoff_latencies: list[int] = []
        self._lock = Lock()

    def send(self, message: AgentMessage) -> None:
        start = time.perf_counter()
        with self._lock:
            self._mailboxes[message.recipient].append(message)
        latency_ms = int((time.perf_counter() - start) * 1000)
        self._handoff_latencies.append(latency_ms)

    def consume(self, recipient: str) -> list[AgentMessage]:
        with self._lock:
            messages = list(self._mailboxes[recipient])
            self._mailboxes[recipient].clear()
        return messages

    def handoff_latencies(self) -> list[int]:
        return list(self._handoff_latencies)
