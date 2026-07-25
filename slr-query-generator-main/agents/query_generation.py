from __future__ import annotations

from typing import Any

from state.research_workflow_state import WorkflowLifecycle


class QueryGenerationAgent:
    agent_id = "query_generation"
    description = "Generates database-ready Boolean queries using registered query tools."

    def __init__(self, tools) -> None:
        self._tools = tools

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        result = self._tools.get("query.generate")(state["topic"])
        query = result["query"]
        return {
            "lifecycle": WorkflowLifecycle.QUERY_GENERATION.value,
            "queries": {
                "google_scholar": query,
                "scopus": f"TITLE-ABS-KEY({query})",
                "web_of_science": f"TS=({query})",
                "ieee_xplore": query,
                "pubmed": query,
            },
            "artifacts": {"query_generation": result},
            "events": [{"agent": self.agent_id, "event": "query_generated", "source": result["source"]}],
        }
