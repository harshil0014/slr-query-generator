from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from repositories.workflow_repository import ResearchWorkflowRepository


class SharedWorkflowMemory:
    """Writes LangGraph state and agent events to Supabase after each node."""

    def __init__(self, repository: ResearchWorkflowRepository) -> None:
        self._repository = repository

    def persist_update(self, previous: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
        merged = dict(previous)
        for key, value in update.items():
            if key in {"events", "errors"}:
                merged[key] = list(previous.get(key, [])) + list(value)
            elif key == "artifacts":
                merged[key] = {**previous.get(key, {}), **value}
            else:
                merged[key] = value
        merged["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._repository.save_state(merged)
        for event in update.get("events", []):
            self._repository.append_event(merged["run_id"], event)
        return merged
