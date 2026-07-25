"""No-network smoke check for the LitSync deduplication adapter."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.deduplication import deduplicate_records


def main() -> None:
    result = deduplicate_records(
        [
            {"title": "Paper A", "doi": "10.1000/ABC", "abstract": "First"},
            {"title": "Paper A duplicate", "doi": "10.1000/abc", "abstract": "Second"},
            {"title": "Paper B", "abstract": "Third"},
            {"title": " paper b ", "abstract": "Duplicate by title"},
        ]
    )
    assert result["input_count"] == 4
    assert result["removed"] == 2
    assert [paper["title"] for paper in result["papers"]] == ["Paper A", "Paper B"]
    print("Deduplication tool smoke check passed.")


if __name__ == "__main__":
    main()
