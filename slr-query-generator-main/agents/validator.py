from __future__ import annotations

from typing import Any

from state.research_workflow_state import WorkflowLifecycle


class ValidatorAgent:
    agent_id = "validator"
    description = "Validates generated queries and records the Phase 1 workflow outcome."

    def __init__(self, tools) -> None:
        self._tools = tools

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        validation = self._tools.get("query.validate")(state.get("queries", {}).get("google_scholar", ""))
        lifecycle = WorkflowLifecycle.COMPLETED if validation["valid"] else WorkflowLifecycle.FAILED
        return {
            "lifecycle": lifecycle.value,
            "validation": validation,
            "events": [{"agent": self.agent_id, "event": "validation_completed", "valid": validation["valid"]}],
        }
