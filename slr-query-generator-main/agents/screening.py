"""Autonomous screening agent backed by the registered screening tool."""

from __future__ import annotations

from typing import Any
import re

from state.research_workflow_state import WorkflowLifecycle


class ScreeningAgent:
    agent_id = "screening"
    description = "Screens retrieved papers through the registered API-backed screening tool."

    def __init__(self, tools) -> None:
        self._tools = tools

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        papers = state.get("deduplicated_results") or state.get("search_results", [])
        result = self._tools.get("screen.run")(
            papers,
            state["topic"],
            inclusion_criteria=state.get("inclusion_criteria", []),
            exclusion_criteria=state.get("exclusion_criteria", []),
            max_rows=state.get("paper_limit", 100),
        )
        screening_results = self._select_best_studies(result["papers"], state)
        summary = result["summary"]
        return {
            "lifecycle": WorkflowLifecycle.SCREENING.value,
            "screening_results": screening_results,
            "artifacts": {
                "screening": {
                    "engine": result["engine"],
                    "summary": summary,
                }
            },
            "events": [
                {
                    "agent": self.agent_id,
                    "event": "screening_completed",
                    "count": len(screening_results),
                }
            ],
        }

    @staticmethod
    def _select_best_studies(papers: list[dict[str, Any]], state: dict[str, Any]) -> list[dict[str, Any]]:
        """Keep only the strongest screened studies, with an auditable reason."""
        target = max(25, min(int(state.get("target_included_papers", 25)), 50))
        topic_terms = set(re.findall(r"[a-z0-9]{3,}", str(state.get("topic", "")).lower()))
        criteria_terms = set()
        for criterion in state.get("inclusion_criteria", []):
            criteria_terms.update(re.findall(r"[a-z0-9]{3,}", str(criterion).lower()))

        def score(paper: dict[str, Any]) -> tuple[int, int, int]:
            text = f"{paper.get('title') or paper.get('Title') or ''} {paper.get('abstract') or paper.get('Abstract') or ''}".lower()
            words = set(re.findall(r"[a-z0-9]{3,}", text))
            relevance = len(words & topic_terms) * 3 + len(words & criteria_terms) * 2
            try:
                cited = int(paper.get("cited_by") or paper.get("Cited by") or 0)
            except (TypeError, ValueError):
                cited = 0
            try:
                year = int(paper.get("publication_year") or paper.get("Year") or 0)
            except (TypeError, ValueError):
                year = 0
            return relevance, cited, year

        eligible = [paper for paper in papers if str(paper.get("Decision") or paper.get("decision") or "").upper() == "KEEP"]
        ranked = sorted(eligible, key=score, reverse=True)
        selected_ids = {id(paper) for paper in ranked[:target]}
        selected_count = min(len(ranked), target)
        normalized: list[dict[str, Any]] = []
        for paper in papers:
            updated = dict(paper)
            if id(paper) in selected_ids:
                updated["Decision"] = "KEEP"
                updated["Reason"] = f"Included: passed screening and ranked in the top {selected_count} for topic and inclusion-criteria relevance."
            elif str(updated.get("Decision") or updated.get("decision") or "").upper() == "KEEP":
                updated["Decision"] = "REJECT"
                updated["Reason"] = f"Rejected after relevance ranking: only the top {target} eligible studies are retained for full-text review."
            normalized.append(updated)
        return normalized
