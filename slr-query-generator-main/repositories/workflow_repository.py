from __future__ import annotations

import os
from typing import Any, Protocol

from state.research_workflow_state import ResearchWorkflowState


class ResearchWorkflowRepository(Protocol):
    def create(self, state: ResearchWorkflowState) -> None: ...
    def get(self, run_id: str) -> dict[str, Any] | None: ...
    def save_state(self, state: dict[str, Any]) -> None: ...
    def append_event(self, run_id: str, event: dict[str, Any]) -> None: ...


class SupabaseWorkflowRepository:
    """Durable memory adapter. Requires SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY."""

    table_name = "research_workflows"
    event_table_name = "research_workflow_events"

    def __init__(self, url: str | None = None, key: str | None = None) -> None:
        url = url or os.getenv("SUPABASE_URL")
        key = key or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required for autonomous workflow memory.")
        try:
            from supabase import create_client
        except ImportError as exc:
            raise RuntimeError("Install requirements.txt to enable Supabase workflow memory.") from exc
        self._client = create_client(url, key)

    def create(self, state: ResearchWorkflowState) -> None:
        payload = state.graph_state()
        self._client.table(self.table_name).insert({
            "id": state.run_id,
            "topic": state.topic,
            "lifecycle": state.lifecycle.value,
            "state": payload,
        }).execute()

    def get(self, run_id: str) -> dict[str, Any] | None:
        response = self._client.table(self.table_name).select("state").eq("id", run_id).limit(1).execute()
        rows = response.data or []
        return rows[0]["state"] if rows else None

    def save_state(self, state: dict[str, Any]) -> None:
        self._client.table(self.table_name).update({
            "lifecycle": state["lifecycle"],
            "state": state,
            "updated_at": state.get("updated_at"),
        }).eq("id", state["run_id"]).execute()

    def append_event(self, run_id: str, event: dict[str, Any]) -> None:
        self._client.table(self.event_table_name).insert({"research_workflow_id": run_id, "event": event}).execute()


class InMemoryWorkflowRepository:
    """Process-local repository for the explicitly enabled local demo mode."""

    def __init__(self) -> None:
        self._states: dict[str, dict[str, Any]] = {}
        self._events: dict[str, list[dict[str, Any]]] = {}

    def create(self, state: ResearchWorkflowState) -> None:
        self._states[state.run_id] = state.graph_state()
        self._events[state.run_id] = []

    def get(self, run_id: str) -> dict[str, Any] | None:
        state = self._states.get(run_id)
        return dict(state) if state else None

    def save_state(self, state: dict[str, Any]) -> None:
        self._states[state["run_id"]] = dict(state)

    def append_event(self, run_id: str, event: dict[str, Any]) -> None:
        self._events.setdefault(run_id, []).append(dict(event))
