"""Agent that creates structured evidence records from included papers."""

from __future__ import annotations

from typing import Any

from state.research_workflow_state import WorkflowLifecycle


class DataExtractionAgent:
    agent_id = "data_extraction"
    description = "Extracts structured evidence from papers included by screening."

    def __init__(self, tools) -> None:
        self._tools = tools

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        included_titles = {
            str(paper.get("Title") or paper.get("title") or "").strip().casefold()
            for paper in state.get("screening_results", [])
            if str(paper.get("Decision") or paper.get("decision") or "").upper() == "KEEP"
        }
        documents = [
            document
            for document in state.get("retrieved_documents", [])
            if str(document.get("title") or "").strip().casefold() in included_titles
        ]
        if not documents:
            documents = [
                {
                    "title": paper.get("title") or paper.get("Title") or "",
                    "doi": paper.get("doi") or paper.get("DOI") or "",
                    "markdown": paper.get("abstract") or paper.get("Abstract") or "",
                }
                for paper in state.get("deduplicated_results") or state.get("search_results", [])
                if str(paper.get("title") or paper.get("Title") or "").strip().casefold()
                in included_titles
            ]
        result = self._tools.get("extract.structured")(documents, state["topic"])
        records = result["records"]
        failures = result["failures"]
        return {
            "lifecycle": WorkflowLifecycle.DATA_EXTRACTION.value,
            "extracted_data": records,
            "artifacts": {
                "data_extraction": {
                    "included_document_count": len(documents),
                    "extracted_count": len(records),
                    "failures": failures,
                }
            },
            "events": [
                {
                    "agent": self.agent_id,
                    "event": "data_extraction_completed",
                    "extracted_count": len(records),
                    "failed_count": len(failures),
                }
            ],
        }
