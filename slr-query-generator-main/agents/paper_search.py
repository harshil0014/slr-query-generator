from __future__ import annotations

import re
from typing import Any

from state.research_workflow_state import WorkflowLifecycle
from tools.scholarly_search import search_registered_providers


class PaperSearchAgent:
    agent_id = "paper_search"
    description = "Searches configured scholarly providers through the Tool Registry."

    def __init__(self, tools) -> None:
        self._tools = tools

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        # Database APIs search better with meaningful terms than a quoted Boolean
        # display query. Keep the display query for the report, but send a broad
        # provider query so that an SLR can collect a substantial candidate set.
        query = self._provider_query(state["topic"])
        providers = state.get("preferred_databases") or ["openalex"]
        paper_limit = max(10, min(int(state.get("paper_limit", 100)), 1000))
        papers = search_registered_providers(
            self._tools,
            providers,
            query,
            from_year=state.get("publication_year_from"),
            to_year=state.get("publication_year_to"),
            limit=paper_limit,
        )[:paper_limit]
        return {
            "lifecycle": WorkflowLifecycle.SEARCHING.value,
            "search_results": papers,
            "events": [{"agent": self.agent_id, "event": "search_completed", "providers": providers, "count": len(papers), "paper_limit": paper_limit}],
        }

    @staticmethod
    def _provider_query(topic: str) -> str:
        terms = re.findall(r"[A-Za-z0-9]{3,}", str(topic))
        ignored = {"and", "for", "the", "with", "based", "using", "into"}
        query_terms = [term for term in terms if term.lower() not in ignored]
        return " ".join(query_terms) or str(topic)
