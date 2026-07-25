"""Retrieve paper content through registered external-provider tools."""

from __future__ import annotations

from typing import Any


class PaperRetrievalAgent:
    agent_id = "paper_retrieval"
    description = "Retrieves available paper content through the Firecrawl tool."

    def __init__(self, tools) -> None:
        self._tools = tools

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        documents: list[dict[str, Any]] = []
        failures: list[dict[str, str]] = []
        # Only retrieve full text for the final screened set. This avoids costly
        # API calls for hundreds of candidates that will be rejected.
        for paper in state.get("screening_results", []):
            if str(paper.get("Decision") or paper.get("decision") or "").upper() != "KEEP":
                continue
            url = str(paper.get("url") or paper.get("Link") or "").strip()
            if not url:
                continue
            try:
                retrieved = self._tools.get("web.retrieve.firecrawl")(url)
                documents.append(
                    {
                        "title": paper.get("title") or paper.get("Title") or "",
                        "doi": paper.get("doi") or paper.get("DOI") or "",
                        **retrieved,
                    }
                )
            except Exception as exc:
                failures.append({"url": url, "message": str(exc)})

        return {
            "retrieved_documents": documents,
            "artifacts": {
                "paper_retrieval": {
                    "retrieved_count": len(documents),
                    "failed_count": len(failures),
                    "failures": failures,
                }
            },
            "events": [
                {
                    "agent": self.agent_id,
                    "event": "retrieval_completed",
                    "retrieved_count": len(documents),
                    "failed_count": len(failures),
                }
            ],
        }
