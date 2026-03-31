from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class ResearchRequest(BaseModel):
    session_id: str = Field(..., min_length=3)
    topic: str = Field(..., min_length=3)
    constraints: list[str] = Field(default_factory=list)


class AgentArtifact(BaseModel):
    agent_name: str
    content: str
    sources: list[str] = Field(default_factory=list)
    latency_ms: int


class OrchestrationResult(BaseModel):
    session_id: str
    topic: str
    summary: str
    critique: str
    artifacts: list[AgentArtifact]
    total_latency_ms: int
    handoff_latencies_ms: list[int]


class Job(BaseModel):
    id: str
    request: ResearchRequest
    status: JobStatus = JobStatus.queued
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    result: OrchestrationResult | None = None
    error: str | None = None


class AgentMessage(BaseModel):
    sender: str
    recipient: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
