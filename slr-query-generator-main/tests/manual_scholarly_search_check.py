"""Standalone smoke check for scholarly provider routing.

The check uses in-memory tools, so no API key, network connection, or pytest is required.
"""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools.registry import ToolRegistry
from tools.scholarly_search import search_registered_providers


def main() -> None:
    registry = ToolRegistry()
    registry.register(
        "search.openalex",
        lambda query, **_: [{"provider": "openalex", "title": query}],
    )
    registry.register(
        "search.arxiv",
        lambda query, **_: (_ for _ in ()).throw(
            NotImplementedError("arXiv is not enabled")
        ),
    )

    records = search_registered_providers(
        registry,
        ["openalex", "arxiv"],
        "Explainable AI in Healthcare",
        from_year=2020,
    )
    assert records == [
        {"provider": "openalex", "title": "Explainable AI in Healthcare"}
    ], records
    print("Scholarly search tool smoke check passed.")


if __name__ == "__main__":
    main()
