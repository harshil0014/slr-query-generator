from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class WorkflowLifecycle(StrEnum):
    CREATED = "CREATED"
    PLANNING = "PLANNING"
    QUERY_GENERATION = "QUERY_GENERATION"
    SEARCHING = "SEARCHING"
    PAPER_RETRIEVAL = "PAPER_RETRIEVAL"
    DEDUPLICATION = "DEDUPLICATION"
    SCREENING = "SCREENING"
    DATA_EXTRACTION = "DATA_EXTRACTION"
    QUALITY_ASSESSMENT = "QUALITY_ASSESSMENT"
    SYNTHESIS = "SYNTHESIS"
    REPORT_GENERATION = "REPORT_GENERATION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    PAUSED = "PAUSED"


class ResearchWorkflowState(BaseModel):
    """Durable, JSON-serializable state shared by every workflow agent."""

    run_id: str = Field(default_factory=lambda: str(uuid4()))
    topic: str
    inclusion_criteria: list[str] = Field(default_factory=list)
    exclusion_criteria: list[str] = Field(default_factory=list)
    preferred_databases: list[str] = Field(default_factory=lambda: ["openalex"])
    paper_limit: int = Field(default=100, ge=10, le=1000)
    target_included_papers: int = Field(default=25, ge=25, le=50)
    publication_year_from: int | None = None
    publication_year_to: int | None = None
    lifecycle: WorkflowLifecycle = WorkflowLifecycle.CREATED
    execution_plan: list[str] = Field(default_factory=list)
    completed_agents: list[str] = Field(default_factory=list)
    next_agent: str | None = None
    queries: dict[str, str] = Field(default_factory=dict)
    search_results: list[dict[str, Any]] = Field(default_factory=list)
    retrieved_documents: list[dict[str, Any]] = Field(default_factory=list)
    deduplicated_results: list[dict[str, Any]] = Field(default_factory=list)
    screening_results: list[dict[str, Any]] = Field(default_factory=list)
    extracted_data: list[dict[str, Any]] = Field(default_factory=list)
    quality_assessments: list[dict[str, Any]] = Field(default_factory=list)
    quality_summary: dict[str, Any] = Field(default_factory=dict)
    synthesis: dict[str, Any] = Field(default_factory=dict)
    validation: dict[str, Any] = Field(default_factory=dict)
    artifacts: dict[str, Any] = Field(default_factory=dict)
    errors: list[dict[str, str]] = Field(default_factory=list)
    events: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def graph_state(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def new(cls, **values: Any) -> "ResearchWorkflowState":
        return cls(**values)
