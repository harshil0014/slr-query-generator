"""No-network smoke check for the Paper Retrieval Agent."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.paper_retrieval import PaperRetrievalAgent
from tools.registry import ToolRegistry


def main() -> None:
    tools = ToolRegistry()
    tools.register(
        "web.retrieve.firecrawl",
        lambda url: {"provider": "firecrawl", "url": url, "markdown": "# Paper"},
    )
    update = PaperRetrievalAgent(tools).execute(
        {
            "search_results": [
                {"title": "Retrievable", "doi": "10.1/test", "url": "https://example.com/paper"},
                {"title": "No URL"},
            ]
        }
    )
    assert update["retrieved_documents"] == [
        {
            "title": "Retrievable",
            "doi": "10.1/test",
            "provider": "firecrawl",
            "url": "https://example.com/paper",
            "markdown": "# Paper",
        }
    ]
    assert update["artifacts"]["paper_retrieval"]["failed_count"] == 0
    print("Paper Retrieval Agent smoke check passed.")


if __name__ == "__main__":
    main()
