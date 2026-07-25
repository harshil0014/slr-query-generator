"""Standalone smoke check for the Search Agent."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.paper_search import PaperSearchAgent
from tools.registry import ToolRegistry


def main() -> None:
    captured: dict[str, object] = {}

    def openalex_search(query: str, **kwargs: object) -> list[dict[str, object]]:
        captured["query"] = query
        captured.update(kwargs)
        return [{"provider": "openalex", "title": "A test paper"}]

    tools = ToolRegistry()
    tools.register("search.openalex", openalex_search)

    update = PaperSearchAgent(tools).execute(
        {
            "topic": "Explainable AI in Healthcare",
            "queries": {"google_scholar": '("Explainable AI" AND "Healthcare")'},
            "preferred_databases": ["openalex"],
            "publication_year_from": 2020,
            "publication_year_to": 2024,
        }
    )
    assert captured == {
        "query": '("Explainable AI" AND "Healthcare")',
        "from_year": 2020,
        "to_year": 2024,
    }, captured
    assert update["search_results"][0]["title"] == "A test paper"
    assert update["events"][0]["count"] == 1
    print("Search Agent smoke check passed.")


if __name__ == "__main__":
    main()
