"""No-network smoke check for the Deduplication Agent."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.deduplication import DeduplicationAgent
from tools.registry import ToolRegistry


def main() -> None:
    tools = ToolRegistry()
    tools.register(
        "deduplicate.run",
        lambda records: {"papers": records[:1], "input_count": len(records), "removed": 1},
    )
    update = DeduplicationAgent(tools).execute(
        {"search_results": [{"title": "Paper A"}, {"title": "Paper A duplicate"}]}
    )
    assert update["deduplicated_results"] == [{"title": "Paper A"}]
    assert update["artifacts"]["deduplication"] == {
        "input_count": 2,
        "removed": 1,
        "output_count": 1,
    }
    print("Deduplication Agent smoke check passed.")


if __name__ == "__main__":
    main()
