"""Standalone smoke check for shared-memory merge and persistence behavior."""

from pathlib import Path
import sys
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from memory.shared_memory import SharedWorkflowMemory


class FakeRepository:
    def __init__(self) -> None:
        self.saved_state: dict[str, Any] | None = None
        self.events: list[tuple[str, dict[str, Any]]] = []

    def save_state(self, state: dict[str, Any]) -> None:
        self.saved_state = state

    def append_event(self, run_id: str, event: dict[str, Any]) -> None:
        self.events.append((run_id, event))


def main() -> None:
    repository = FakeRepository()
    memory = SharedWorkflowMemory(repository)
    merged = memory.persist_update(
        {
            "run_id": "memory-smoke-check",
            "events": [{"event": "created"}],
            "errors": [],
            "artifacts": {"planner": {"status": "done"}},
        },
        {
            "events": [{"event": "planned"}],
            "artifacts": {"query": {"status": "done"}},
        },
    )

    assert [event["event"] for event in merged["events"]] == ["created", "planned"]
    assert set(merged["artifacts"]) == {"planner", "query"}
    assert repository.saved_state == merged
    assert repository.events == [("memory-smoke-check", {"event": "planned"})]
    print("Shared workflow memory smoke check passed.")


if __name__ == "__main__":
    main()
