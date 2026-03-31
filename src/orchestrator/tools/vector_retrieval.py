from __future__ import annotations


class VectorRetrievalTool:
    name = "vector_retrieval"

    def __init__(self, fake_results: bool = True) -> None:
        self._fake_results = fake_results

    def run(self, query: str) -> str:
        if self._fake_results:
            return f"Simulated vector retrieval snippets for: {query}"
        return "Vector retrieval backend not configured."
