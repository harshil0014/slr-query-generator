from __future__ import annotations

from typing import Any, Callable

ToolCallable = Callable[..., Any]


class ToolRegistry:
    """Provider-agnostic tool boundary used by all workflow agents."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolCallable] = {}

    def register(self, tool_id: str, tool: ToolCallable) -> None:
        if tool_id in self._tools:
            raise ValueError(f"Tool already registered: {tool_id}")
        self._tools[tool_id] = tool

    def get(self, tool_id: str) -> ToolCallable:
        try:
            return self._tools[tool_id]
        except KeyError as exc:
            raise KeyError(f"Unknown tool: {tool_id}") from exc

    def ids(self) -> tuple[str, ...]:
        return tuple(self._tools)


_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    return _registry
