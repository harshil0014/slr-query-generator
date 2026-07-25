"""No-network end-to-end smoke check for the Phase 1 LangGraph workflow."""

from pathlib import Path
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.paper_search import PaperSearchAgent
from agents.planner import PlannerAgent
from agents.query_generation import QueryGenerationAgent
from agents.registry import AgentRegistry
from agents.validator import ValidatorAgent
from tools.registry import ToolRegistry
from workflows.research_workflow import build_research_workflow


class InMemoryWorkflowMemory:
    def __init__(self) -> None:
        self.updates: list[dict[str, Any]] = []

    def persist_update(
        self, previous: dict[str, Any], update: dict[str, Any]
    ) -> dict[str, Any]:
        self.updates.append(update)
        return {**previous, **update}


def main() -> None:
    tools = ToolRegistry()
    tools.register(
        "query.generate",
        lambda _: {"query": '("Explainable AI" AND "Healthcare")', "source": "test"},
    )
    tools.register(
        "query.validate", lambda _: {"valid": True, "errors": []}
    )
    tools.register(
        "search.openalex",
        lambda query, **_: [{"provider": "openalex", "title": query}],
    )

    registry = AgentRegistry()
    registry.register(PlannerAgent(registry))
    registry.register(QueryGenerationAgent(tools))
    registry.register(PaperSearchAgent(tools))
    registry.register(ValidatorAgent(tools))

    memory = InMemoryWorkflowMemory()
    workflow = build_research_workflow(memory, registry)
    final_state = workflow.invoke(
        {
            "run_id": "phase1-smoke-check",
            "topic": "Explainable AI in Healthcare",
            "preferred_databases": ["openalex"],
            "events": [],
            "errors": [],
            "artifacts": {},
        }
    )

    assert final_state["lifecycle"] == "COMPLETED", final_state
    assert final_state["completed_agents"] == [
        "planner",
        "query_generation",
        "paper_search",
        "validator",
    ], final_state
    assert len(final_state["events"]) == 4, final_state["events"]
    assert final_state["search_results"][0]["provider"] == "openalex"
    assert len(memory.updates) == 4, memory.updates
    print("Phase 1 LangGraph workflow smoke check passed.")


if __name__ == "__main__":
    main()
