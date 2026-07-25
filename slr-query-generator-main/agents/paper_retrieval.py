"""Retrieve paper content through registered external-provider tools."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
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
        selected: list[dict[str, Any]] = []
        for paper in state.get("screening_results", []):
            if str(paper.get("Decision") or paper.get("decision") or "").upper() != "KEEP":
                continue
            url = str(paper.get("url") or paper.get("Link") or "").strip()
            if not url:
                failures.append({"url": "", "message": "No paper link was provided."})
                continue
            selected.append(paper)

        # Do not attempt network calls when full-text enrichment has not been
        # configured. The later agents can still finish using real metadata.
        if not os.getenv("FIRECRAWL_API_KEY"):
            failures.extend({
                "url": str(paper.get("url") or paper.get("Link") or ""),
                "message": "Skipped: FIRECRAWL_API_KEY is not configured.",
            } for paper in selected)
        else:
            workers = max(1, min(int(os.getenv("FULL_TEXT_RETRIEVAL_WORKERS", "5")), 10))
            with ThreadPoolExecutor(max_workers=workers) as executor:
                jobs = {
                    executor.submit(self._tools.get("web.retrieve.firecrawl"), str(paper.get("url") or paper.get("Link"))): paper
                    for paper in selected
                }
                for future in as_completed(jobs):
                    paper = jobs[future]
                    url = str(paper.get("url") or paper.get("Link") or "")
                    try:
                        retrieved = future.result()
                        documents.append({
                            "title": paper.get("title") or paper.get("Title") or "",
                            "doi": paper.get("doi") or paper.get("DOI") or "",
                            **retrieved,
                        })
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
