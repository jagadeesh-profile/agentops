from __future__ import annotations

import time
from typing import TypedDict

from orchestrator.agents import CritiqueAgent, RetrievalAgent, SynthesisAgent
from orchestrator.messaging import AutoGenMessageBus
from orchestrator.models import AgentMessage, OrchestrationResult, ResearchRequest


class WorkflowState(TypedDict):
    session_id: str
    topic: str
    retrieval: str
    synthesis: str
    critique: str


class MultiAgentWorkflow:
    def __init__(
        self,
        retrieval_agent: RetrievalAgent,
        synthesis_agent: SynthesisAgent,
        critique_agent: CritiqueAgent,
        message_bus: AutoGenMessageBus,
    ) -> None:
        self.retrieval_agent = retrieval_agent
        self.synthesis_agent = synthesis_agent
        self.critique_agent = critique_agent
        self.message_bus = message_bus
        self._compiled_graph = self._build_graph_if_available()

    def _build_graph_if_available(self):
        try:
            from langgraph.graph import END, StateGraph
        except Exception:
            return None

        graph = StateGraph(WorkflowState)

        def retrieval_node(state: WorkflowState):
            artifact = self.retrieval_agent.run(state["session_id"], state["topic"])
            self.message_bus.send(
                AgentMessage(
                    sender="retrieval",
                    recipient="synthesis",
                    content=artifact.content,
                    metadata={"latency_ms": artifact.latency_ms},
                )
            )
            return {"retrieval": artifact.content}

        def synthesis_node(state: WorkflowState):
            artifact = self.synthesis_agent.run(
                state["session_id"], state["topic"], prior_output=state.get("retrieval", "")
            )
            self.message_bus.send(
                AgentMessage(
                    sender="synthesis",
                    recipient="critique",
                    content=artifact.content,
                    metadata={"latency_ms": artifact.latency_ms},
                )
            )
            return {"synthesis": artifact.content}

        def critique_node(state: WorkflowState):
            artifact = self.critique_agent.run(
                state["session_id"], state["topic"], prior_output=state.get("synthesis", "")
            )
            return {"critique": artifact.content}

        graph.add_node("retrieval", retrieval_node)
        graph.add_node("synthesis", synthesis_node)
        graph.add_node("critique", critique_node)
        graph.set_entry_point("retrieval")
        graph.add_edge("retrieval", "synthesis")
        graph.add_edge("synthesis", "critique")
        graph.add_edge("critique", END)
        return graph.compile()

    def run(self, req: ResearchRequest) -> OrchestrationResult:
        start = time.perf_counter()

        retrieval_artifact = self.retrieval_agent.run(req.session_id, req.topic)
        self.message_bus.send(
            AgentMessage(
                sender="retrieval",
                recipient="synthesis",
                content=retrieval_artifact.content,
                metadata={"latency_ms": retrieval_artifact.latency_ms},
            )
        )

        synthesis_artifact = self.synthesis_agent.run(
            req.session_id, req.topic, prior_output=retrieval_artifact.content
        )
        self.message_bus.send(
            AgentMessage(
                sender="synthesis",
                recipient="critique",
                content=synthesis_artifact.content,
                metadata={"latency_ms": synthesis_artifact.latency_ms},
            )
        )

        critique_artifact = self.critique_agent.run(
            req.session_id, req.topic, prior_output=synthesis_artifact.content
        )

        if self._compiled_graph is not None:
            _ = self._compiled_graph.invoke(
                {
                    "session_id": req.session_id,
                    "topic": req.topic,
                    "retrieval": retrieval_artifact.content,
                    "synthesis": synthesis_artifact.content,
                    "critique": critique_artifact.content,
                }
            )

        return OrchestrationResult(
            session_id=req.session_id,
            topic=req.topic,
            summary=synthesis_artifact.content,
            critique=critique_artifact.content,
            artifacts=[retrieval_artifact, synthesis_artifact, critique_artifact],
            total_latency_ms=int((time.perf_counter() - start) * 1000),
            handoff_latencies_ms=self.message_bus.handoff_latencies(),
        )
