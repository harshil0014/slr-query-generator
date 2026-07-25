from __future__ import annotations

from typing import Any

from state.research_workflow_state import WorkflowLifecycle


class PlannerAgent:
    agent_id = "planner"
    description = "Builds an executable research plan from agents currently registered."

    def __init__(self, registry) -> None:
        self._registry = registry

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        # The plan is intentionally registry-driven: adding an agent does not require changing this workflow.
        preferred_sequence = (
            "query_generation",
            "paper_search",
            "deduplication",
            "screening",
            "paper_retrieval",
            "data_extraction",
            "quality_assessment",
            "evidence_synthesis",
            "validator",
            "report_generation",
        )
        available = set(self._registry.ids())
        plan = [agent_id for agent_id in preferred_sequence if agent_id in available]
        if not plan:
            raise RuntimeError("No executable research agents are registered.")
        return {
            "lifecycle": WorkflowLifecycle.PLANNING.value,
            "execution_plan": plan,
            "completed_agents": ["planner"],
            "next_agent": plan[0],
            "events": [{"agent": self.agent_id, "event": "planned", "plan": plan}],
        }
