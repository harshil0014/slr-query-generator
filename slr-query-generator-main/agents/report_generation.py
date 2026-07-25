"""Final active agent for the demo workflow."""

from __future__ import annotations

from typing import Any

from state.research_workflow_state import WorkflowLifecycle


class ReportGenerationAgent:
    agent_id = "report_generation"
    description = "Generates the final downloadable systematic literature review report."

    def __init__(self, tools) -> None:
        self._tools = tools

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        report = self._tools.get("report.generate")(state)
        csv_exports = self._tools.get("review.export_csvs")(state)
        return {
            "lifecycle": WorkflowLifecycle.COMPLETED.value,
            "artifacts": {"report": report, "csv_exports": csv_exports},
            "events": [{"agent": self.agent_id, "event": "report_generated"}],
        }
