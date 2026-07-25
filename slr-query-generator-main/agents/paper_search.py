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
        providers = state.get("preferred_databases") or ["openalex"]
        paper_limit = max(10, min(int(state.get("paper_limit", 100)), 1000))
        papers: list[dict[str, Any]] = []
        seen: set[str] = set()
        queries_used: list[str] = []
        for query in self._provider_queries(state["topic"]):
            remaining = paper_limit - len(papers)
            if remaining <= 0:
                break
            candidates = search_registered_providers(
                self._tools,
                providers,
                query,
                from_year=state.get("publication_year_from"),
                to_year=state.get("publication_year_to"),
                limit=remaining,
            )
            queries_used.append(query)
            for paper in candidates:
                identity = self._identity(paper)
                if identity not in seen:
                    seen.add(identity)
                    papers.append(paper)
                    if len(papers) == paper_limit:
                        break
        if len(papers) < paper_limit:
            raise RuntimeError(
                f"Only {len(papers)} unique real papers were found after expanding the search; "
                f"{paper_limit} were requested. Refine the topic or lower the candidate count."
            )
        return {
            "lifecycle": WorkflowLifecycle.SEARCHING.value,
            "search_results": papers,
            "artifacts": {"paper_search": {"requested_count": paper_limit, "returned_count": len(papers), "queries_used": queries_used}},
            "events": [{"agent": self.agent_id, "event": "search_completed", "providers": providers, "count": len(papers), "paper_limit": paper_limit, "queries_used": queries_used}],
        }

    @staticmethod
    def _provider_queries(topic: str) -> list[str]:
        terms = re.findall(r"[A-Za-z0-9]{3,}", str(topic))
        ignored = {"and", "for", "the", "with", "based", "using", "into"}
        query_terms = [term for term in terms if term.lower() not in ignored]
        full_query = " ".join(query_terms) or str(topic)
        # The first query is precise. Later queries intentionally use only the
        # most informative concepts to collect enough real SLR candidates.
        queries = [full_query]
        for width in (4, 3, 2):
            if len(query_terms) >= width:
                queries.append(" ".join(query_terms[:width]))
        if len(query_terms) >= 4:
            queries.append(" ".join(query_terms[-4:]))
        return list(dict.fromkeys(query for query in queries if query.strip()))

    @staticmethod
    def _identity(paper: dict[str, Any]) -> str:
        doi = str(paper.get("doi") or paper.get("DOI") or "").strip().casefold()
        if doi:
            return f"doi:{doi}"
        title = str(paper.get("title") or paper.get("Title") or "").strip().casefold()
        year = str(paper.get("publication_year") or paper.get("Year") or "").strip()
        return f"title:{title}|{year}"
