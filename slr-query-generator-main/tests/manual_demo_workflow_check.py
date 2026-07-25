"""No-network end-to-end check for the six-agent hackathon demo workflow."""

from pathlib import Path
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.data_extraction import DataExtractionAgent
from agents.paper_search import PaperSearchAgent
from agents.planner import PlannerAgent
from agents.query_generation import QueryGenerationAgent
from agents.registry import AgentRegistry
from agents.report_generation import ReportGenerationAgent
from agents.screening import ScreeningAgent
from tools.registry import ToolRegistry
from tools.reporting import generate_report
from workflows.research_workflow import build_research_workflow


class InMemoryWorkflowMemory:
    def __init__(self) -> None:
        self.updates: list[dict[str, Any]] = []

    def persist_update(self, previous: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
        self.updates.append(update)
        return {**previous, **update}


def main() -> None:
    tools = ToolRegistry()
    tools.register("query.generate", lambda _: {"query": '"Explainable AI"', "source": "test"})
    tools.register(
        "search.openalex",
        lambda query, **_: [{"title": "A study", "abstract": "Evidence", "doi": "10.1/test"}],
    )
    tools.register(
        "screen.run",
        lambda papers, question, **_: {
            "engine": "gemini_api", "summary": {"keep": 1},
            "papers": [{"Title": papers[0]["title"], "Decision": "KEEP", "Reason": "Relevant"}],
        },
    )
    tools.register(
        "extract.structured",
        lambda documents, topic: {
            "records": [{"title": documents[0]["title"], "methodology": "Review", "key_findings": "Useful"}],
            "failures": [],
        },
    )
    tools.register("report.generate", generate_report)

    registry = AgentRegistry()
    registry.register(PlannerAgent(registry))
    registry.register(QueryGenerationAgent(tools))
    registry.register(PaperSearchAgent(tools))
    registry.register(ScreeningAgent(tools))
    registry.register(DataExtractionAgent(tools))
    registry.register(ReportGenerationAgent(tools))

    memory = InMemoryWorkflowMemory()
    final_state = build_research_workflow(memory, registry).invoke(
        {
            "run_id": "demo-workflow-check",
            "topic": "Explainable AI in Healthcare",
            "preferred_databases": ["openalex"],
            "events": [], "errors": [], "artifacts": {},
        }
    )
    assert final_state["lifecycle"] == "COMPLETED", final_state
    assert final_state["completed_agents"] == [
        "planner", "query_generation", "paper_search", "screening",
        "data_extraction", "report_generation",
    ], final_state
    assert "# Systematic Literature Review" in final_state["artifacts"]["report"]["markdown"]
    assert len(memory.updates) == 6
    print("Hackathon demo workflow check passed.")


if __name__ == "__main__":
    main()
