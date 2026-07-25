from __future__ import annotations

from typing import Any

from agents.bootstrap import bootstrap_registries
from memory.shared_memory import SharedWorkflowMemory
from repositories.workflow_repository import ResearchWorkflowRepository
from state.research_workflow_state import ResearchWorkflowState
from workflows.research_workflow import build_research_workflow


class ResearchWorkflowService:
    def __init__(self, repository: ResearchWorkflowRepository) -> None:
        self._repository = repository
        self._memory = SharedWorkflowMemory(repository)

    def start(self, state: ResearchWorkflowState) -> str:
        self.create(state)
        self.execute(state)
        return state.run_id

    def create(self, state: ResearchWorkflowState) -> str:
        self._repository.create(state)
        return state.run_id

    def execute(self, state: ResearchWorkflowState) -> None:
        bootstrap_registries()
        graph = build_research_workflow(self._memory)
        graph.invoke(state.graph_state())

    def get(self, run_id: str) -> dict[str, Any] | None:
        return self._repository.get(run_id)
