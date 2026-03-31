from __future__ import annotations

from typing import Protocol


class Tool(Protocol):
    name: str

    def run(self, query: str) -> str:
        ...


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def run(self, tool_name: str, query: str) -> str:
        tool = self._tools.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        return tool.run(query)
