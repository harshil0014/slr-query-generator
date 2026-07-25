"""Standalone smoke check for the Query Generation Agent."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.query_generation import QueryGenerationAgent
from tools.registry import ToolRegistry


def main() -> None:
    tools = ToolRegistry()
    tools.register(
        "query.generate",
        lambda topic: {
            "query": '("Explainable AI" AND "Healthcare")',
            "source": "test",
        },
    )

    update = QueryGenerationAgent(tools).execute(
        {"topic": "Explainable AI in Healthcare"}
    )
    assert update["queries"]["scopus"] == (
        'TITLE-ABS-KEY(("Explainable AI" AND "Healthcare"))'
    )
    assert update["artifacts"]["query_generation"]["source"] == "test"
    print("Query Generation Agent smoke check passed.")


if __name__ == "__main__":
    main()
