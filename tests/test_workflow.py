from orchestrator.agents import CritiqueAgent, RetrievalAgent, SynthesisAgent
from orchestrator.memory.store import PersistentMemoryStore
from orchestrator.messaging import AutoGenMessageBus
from orchestrator.models import ResearchRequest
from orchestrator.tools.code_executor import CodeExecutionTool
from orchestrator.tools.registry import ToolRegistry
from orchestrator.tools.vector_retrieval import VectorRetrievalTool
from orchestrator.tools.web_search import WebSearchTool
from orchestrator.workflow import MultiAgentWorkflow


def test_workflow_runs_end_to_end(tmp_path):
    memory = PersistentMemoryStore(str(tmp_path / "memory.db"))
    tools = ToolRegistry()
    tools.register(WebSearchTool(fake_results=True))
    tools.register(VectorRetrievalTool(fake_results=True))
    tools.register(CodeExecutionTool())

    workflow = MultiAgentWorkflow(
        retrieval_agent=RetrievalAgent("retrieval", memory, tools),
        synthesis_agent=SynthesisAgent("synthesis", memory, tools),
        critique_agent=CritiqueAgent("critique", memory, tools),
        message_bus=AutoGenMessageBus(),
    )

    result = workflow.run(ResearchRequest(session_id="session-1", topic="Agentic research automation"))

    assert result.session_id == "session-1"
    assert len(result.artifacts) == 3
    assert result.total_latency_ms >= 0
