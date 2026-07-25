"""Autonomous agent for the existing LitSync deduplication capability."""

from __future__ import annotations

from typing import Any


class DeduplicationAgent:
    agent_id = "deduplication"
    description = "Deduplicates retrieved papers through the registered LitSync tool."

    def __init__(self, tools) -> None:
        self._tools = tools

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        result = self._tools.get("deduplicate.run")(state.get("search_results", []))
        papers = result["papers"]
        return {
            "deduplicated_results": papers,
            "artifacts": {
                "deduplication": {
                    "input_count": result["input_count"],
                    "removed": result["removed"],
                    "output_count": len(papers),
                }
            },
            "events": [
                {
                    "agent": self.agent_id,
                    "event": "deduplication_completed",
                    "input_count": result["input_count"],
                    "removed": result["removed"],
                }
            ],
        }
