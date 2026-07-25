"""Lightweight quality assessment agent that scores included papers."""

from __future__ import annotations

from typing import Any

from state.research_workflow_state import WorkflowLifecycle


class QualityAssessmentAgent:
    agent_id = "quality_assessment"
    description = "Scores methodological quality of included studies using registered quality tools."

    def __init__(self, tools) -> None:
        self._tools = tools

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        included_titles = {
            str(paper.get("Title") or paper.get("title") or "").strip().casefold()
            for paper in state.get("screening_results", [])
            if str(paper.get("Decision") or paper.get("decision") or "").upper() == "KEEP"
        }

        papers_to_assess = [
            paper
            for paper in state.get("deduplicated_results") or state.get("search_results", [])
            if str(paper.get("title") or paper.get("Title") or "").strip().casefold() in included_titles
        ]

        if not papers_to_assess:
            papers_to_assess = [
                {"title": r.get("title", ""), "abstract": r.get("abstract", "")}
                for r in state.get("extracted_data", [])
            ]

        result = self._tools.get("quality.assess")(papers_to_assess, state["topic"])
        assessments = result.get("assessments", [])
        summary = result.get("summary", {})

        return {
            "lifecycle": WorkflowLifecycle.QUALITY_ASSESSMENT.value,
            "quality_assessments": assessments,
            "quality_summary": summary,
            "artifacts": {
                "quality_assessment": {
                    "papers_assessed": summary.get("papers_assessed", 0),
                    "average_score": summary.get("average_quality_score", 0.0),
                    "summary": summary,
                }
            },
            "events": [
                {
                    "agent": self.agent_id,
                    "event": "quality_assessment_completed",
                    "papers_assessed": len(assessments),
                    "average_score": summary.get("average_quality_score", 0.0),
                }
            ],
        }
