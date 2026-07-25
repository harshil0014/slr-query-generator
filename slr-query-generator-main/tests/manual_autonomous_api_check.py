"""Standalone smoke check for autonomous API behavior without FastAPI startup."""

from pathlib import Path
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import BackgroundTasks, HTTPException

import api.autonomous_routes as routes


class FakeWorkflowService:
    def __init__(self) -> None:
        self.created: list[str] = []
        self.executed: list[str] = []

    def create(self, state: Any) -> str:
        self.created.append(state.run_id)
        return state.run_id

    def execute(self, state: Any) -> None:
        self.executed.append(state.run_id)

    def get(self, run_id: str) -> dict[str, Any] | None:
        return {
            "run_id": run_id,
            "artifacts": {"report": {"markdown": "# Demo Report\n"}},
        }


def main() -> None:
    service = FakeWorkflowService()
    original_service_factory = routes._service
    routes._service = lambda: service
    try:
        health = routes.autonomous_health()
        assert health["status"] == "ready"

        background_tasks = BackgroundTasks()
        response = routes.create_research_run(
            routes.ResearchRunRequest(topic="Explainable AI in Healthcare"),
            background_tasks,
        )
        assert response["next_agent"] == "planner"
        assert response["workflow_version"] == routes.WORKFLOW_VERSION
        assert response["run_id"] in service.created
        assert response["created_at"] is not None
        assert len(background_tasks.tasks) == 1
        task = background_tasks.tasks[0]
        task.func(*task.args, **task.kwargs)
        assert response["run_id"] in service.executed

        report = routes.get_research_run_report(response["run_id"])
        assert report.body == b"# Demo Report\n"

        try:
            routes.resume_research_run(response["run_id"])
        except HTTPException as exc:
            assert exc.status_code == 501
        else:
            raise AssertionError("Resume endpoint must return HTTP 501 until implemented.")
    finally:
        routes._service = original_service_factory
    print("Autonomous API smoke check passed.")


if __name__ == "__main__":
    main()
