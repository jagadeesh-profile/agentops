from __future__ import annotations


class CodeExecutionTool:
    name = "code_execution"

    def run(self, query: str) -> str:
        return f"Code execution stub received task: {query}"
