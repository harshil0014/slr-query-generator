from __future__ import annotations

import logging
import os

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from repositories.workflow_repository import InMemoryWorkflowRepository, SupabaseWorkflowRepository
from services.workflow_service import ResearchWorkflowService
from state.research_workflow_state import ResearchWorkflowState

router = APIRouter(prefix="/api/v1", tags=["autonomous-research"])
logger = logging.getLogger(__name__)
WORKFLOW_VERSION = "1.0.0"
_local_repository = InMemoryWorkflowRepository()


class ResearchRunRequest(BaseModel):
    topic: str = Field(min_length=3)
    inclusion_criteria: list[str] = Field(default_factory=list)
    exclusion_criteria: list[str] = Field(default_factory=list)
    preferred_databases: list[str] = Field(default_factory=lambda: ["openalex"])
    paper_limit: int = Field(default=100, ge=10, le=1000, description="Number of candidate papers to screen (10-1000).")
    target_included_papers: int = Field(default=25, ge=25, le=50, description="Maximum high-relevance studies to include (25-50).")
    publication_year_from: int | None = Field(default=None, ge=1600)
    publication_year_to: int | None = Field(default=None, ge=1600)


def _service() -> ResearchWorkflowService:
    try:
        if os.getenv("AUTONOMOUS_LOCAL_MODE", "").lower() in {"1", "true", "yes"} or os.getenv("AUTONOMOUS_IN_MEMORY_STORAGE", "").lower() in {"1", "true", "yes"}:
            return ResearchWorkflowService(_local_repository)
        return ResearchWorkflowService(SupabaseWorkflowRepository())
    except RuntimeError as exc:
        logger.warning(
            "autonomous_service_unavailable",
            extra={"operation": "create_workflow_service", "error_type": type(exc).__name__},
        )
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.get("/health")
def autonomous_health():
    """Readiness check for autonomous workflow configuration and construction."""
    _service()
    return {
        "status": "ready",
        "workflow_version": WORKFLOW_VERSION,
        "components": {"workflow_service": "ready", "repository": "configured"},
    }


@router.post("/research-runs", status_code=status.HTTP_202_ACCEPTED)
def create_research_run(request: ResearchRunRequest, background_tasks: BackgroundTasks):
    if request.publication_year_from and request.publication_year_to and request.publication_year_from > request.publication_year_to:
        logger.warning(
            "invalid_research_run_request",
            extra={"operation": "create_research_run", "reason": "invalid_publication_year_range"},
        )
        raise HTTPException(status_code=422, detail="publication_year_from must not exceed publication_year_to.")
    state = ResearchWorkflowState.new(**request.model_dump())
    try:
        service = _service()
        service.create(state)
        background_tasks.add_task(service.execute, state)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "research_run_start_failed",
            extra={"operation": "create_research_run", "run_id": state.run_id, "error_type": type(exc).__name__},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to start the research workflow.",
        ) from exc
    return {
        "run_id": state.run_id,
        "status": "accepted",
        "lifecycle": state.lifecycle.value,
        "created_at": state.created_at,
        "next_agent": "planner",
        "workflow_version": WORKFLOW_VERSION,
    }


@router.get("/research-runs/{run_id}")
def get_research_run(run_id: str):
    workflow = _service().get(run_id)
    if workflow is None:
        logger.warning(
            "research_run_not_found",
            extra={"operation": "get_research_run", "run_id": run_id},
        )
        raise HTTPException(status_code=404, detail="Research run not found.")
    return workflow


def _not_implemented(operation: str, run_id: str):
    logger.info(
        "autonomous_endpoint_not_implemented",
        extra={"operation": operation, "run_id": run_id},
    )
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=f"{operation} is planned for a later workflow phase.",
    )


@router.post("/research-runs/{run_id}/resume")
def resume_research_run(run_id: str):
    _not_implemented("resume_research_run", run_id)


@router.get("/research-runs/{run_id}/papers")
def get_research_run_papers(run_id: str):
    _not_implemented("get_research_run_papers", run_id)


@router.get("/research-runs/{run_id}/artifacts")
def get_research_run_artifacts(run_id: str):
    _not_implemented("get_research_run_artifacts", run_id)


@router.get("/research-runs/{run_id}/report")
def get_research_run_report(run_id: str):
    workflow = _service().get(run_id)
    if workflow is None:
        logger.warning(
            "research_run_not_found",
            extra={"operation": "get_research_run_report", "run_id": run_id},
        )
        raise HTTPException(status_code=404, detail="Research run not found.")
    report = (workflow.get("artifacts") or {}).get("report") or {}
    markdown = report.get("markdown")
    if not markdown:
        logger.info(
            "research_report_not_ready",
            extra={"operation": "get_research_run_report", "run_id": run_id},
        )
        raise HTTPException(status_code=404, detail="Research report is not ready.")
    return PlainTextResponse(
        markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="research-report-{run_id}.md"'},
    )


@router.post("/research-runs/{run_id}/review")
def review_research_run(run_id: str):
    _not_implemented("review_research_run", run_id)
