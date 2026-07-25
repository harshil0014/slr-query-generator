"""Standalone smoke check for the Validator Agent."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.validator import ValidatorAgent
from tools.registry import ToolRegistry


def run_case(validation: dict[str, object]) -> dict[str, object]:
    tools = ToolRegistry()
    tools.register("query.validate", lambda _: validation)
    return ValidatorAgent(tools).execute(
        {"queries": {"google_scholar": '("Explainable AI" AND "Healthcare")'}}
    )


def main() -> None:
    valid_update = run_case({"valid": True, "errors": []})
    invalid_update = run_case({"valid": False, "errors": ["Query is empty."]})

    assert valid_update["lifecycle"] == "COMPLETED"
    assert invalid_update["lifecycle"] == "FAILED"
    print("Validator Agent smoke check passed.")


if __name__ == "__main__":
    main()
