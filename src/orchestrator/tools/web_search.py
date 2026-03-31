from __future__ import annotations

import httpx


class WebSearchTool:
    name = "web_search"

    def __init__(self, fake_results: bool = True) -> None:
        self._fake_results = fake_results

    def run(self, query: str) -> str:
        if self._fake_results:
            return f"Simulated web result for: {query}"
        response = httpx.get("https://duckduckgo.com", params={"q": query}, timeout=5)
        response.raise_for_status()
        return f"Live web search response length: {len(response.text)}"
