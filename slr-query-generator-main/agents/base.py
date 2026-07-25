from __future__ import annotations

from typing import Any, Protocol


class WorkflowAgent(Protocol):
    agent_id: str
    description: str

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        """Return a partial LangGraph state update."""
