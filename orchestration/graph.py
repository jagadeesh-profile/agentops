from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from agents.retriever import RetrieverAgent
from agents.analyst import AnalystAgent
from agents.critic import CriticAgent
from agents.synthesizer import SynthesizerAgent


class ResearchState(TypedDict):
    query: str
    retrieved_docs: List[str]
    analysis: str
    critique: str
    final_report: str
    iteration: int


def build_graph():
    retriever = RetrieverAgent()
    analyst = AnalystAgent()
    critic = CriticAgent()
    synthesizer = SynthesizerAgent()

    graph = StateGraph(ResearchState)

    graph.add_node("retrieve", retriever.run)
    graph.add_node("analyze", analyst.run)
    graph.add_node("review", critic.run)       # node name differs from state key "critique"
    graph.add_node("synthesize", synthesizer.run)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "analyze")
    graph.add_edge("analyze", "review")
    graph.add_conditional_edges(
        "review",
        lambda state: "synthesize" if state["iteration"] >= 1 else "retrieve",
        {"synthesize": "synthesize", "retrieve": "retrieve"}
    )
    graph.add_edge("synthesize", END)

    return graph.compile()


research_graph = build_graph()
