"""Agent that synthesizes extracted evidence into themes, gaps, and future work."""

from __future__ import annotations

from typing import Any

from state.research_workflow_state import WorkflowLifecycle


class EvidenceSynthesisAgent:
    agent_id = "evidence_synthesis"
    description = "Synthesizes extracted evidence into executive summary, themes, gaps, and future work."

    def __init__(self, tools) -> None:
        self._tools = tools

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        extracted_data = state.get("extracted_data", [])
        quality_summary = state.get("quality_summary")

        result = self._tools.get("synthesize.evidence")(
            extracted_data,
            state["topic"],
            quality_summary=quality_summary,
        )

        return {
            "lifecycle": WorkflowLifecycle.SYNTHESIS.value,
            "synthesis": result,
            "artifacts": {
                "synthesis": {
                    "has_executive_summary": bool(result.get("executive_summary")),
                    "theme_count": len(result.get("key_themes", [])),
                    "gap_count": len(result.get("research_gaps", [])),
                    "future_work_count": len(result.get("future_work", [])),
                }
            },
            "events": [
                {
                    "agent": self.agent_id,
                    "event": "synthesis_completed",
                    "theme_count": len(result.get("key_themes", [])),
                }
            ],
        }
