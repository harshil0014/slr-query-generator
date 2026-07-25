"""No-network integration check for the workflow with deduplication and screening."""

from pathlib import Path
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.deduplication import DeduplicationAgent
from agents.paper_search import PaperSearchAgent
from agents.planner import PlannerAgent
from agents.query_generation import QueryGenerationAgent
from agents.registry import AgentRegistry
from agents.screening import ScreeningAgent
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
        "query.generate", lambda _: {"query": '"Explainable AI"', "source": "test"}
    )
    tools.register("query.validate", lambda _: {"valid": True, "errors": []})
    tools.register(
        "search.openalex",
        lambda query, **_: [
            {"provider": "openalex", "title": query, "abstract": "A test"},
            {"provider": "openalex", "title": query, "abstract": "Duplicate"},
        ],
    )
    tools.register(
        "deduplicate.run",
        lambda records: {"papers": records[:1], "input_count": len(records), "removed": 1},
    )
    tools.register(
        "screen.run",
        lambda papers, question, **_: {
            "engine": "gemini_api",
            "summary": {"keep": len(papers)},
            "papers": [{"Title": papers[0]["title"], "Decision": "KEEP"}],
        },
    )

    registry = AgentRegistry()
    registry.register(PlannerAgent(registry))
    registry.register(QueryGenerationAgent(tools))
    registry.register(PaperSearchAgent(tools))
    registry.register(DeduplicationAgent(tools))
    registry.register(ScreeningAgent(tools))
    registry.register(ValidatorAgent(tools))

    memory = InMemoryWorkflowMemory()
    final_state = build_research_workflow(memory, registry).invoke(
        {
            "run_id": "deduplication-workflow-check",
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
        "deduplication",
        "screening",
        "validator",
    ], final_state
    assert len(final_state["deduplicated_results"]) == 1
    assert final_state["screening_results"][0]["Decision"] == "KEEP"
    assert len(memory.updates) == 6
    print("Deduplication workflow integration check passed.")


if __name__ == "__main__":
    main()
