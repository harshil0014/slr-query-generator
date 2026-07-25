"""No-network smoke check for Tavily and Firecrawl provider adapters."""

from pathlib import Path
import sys
from unittest.mock import patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from providers.web_research import FirecrawlProvider, TavilyProvider
from tools.registry import ToolRegistry
from tools.web_research import register_web_research_tools


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


def main() -> None:
    registry = ToolRegistry()
    register_web_research_tools(registry)
    assert registry.ids() == ("web.search.tavily", "web.retrieve.firecrawl")

    with patch(
        "providers.web_research.httpx.post",
        return_value=FakeResponse({"results": [{"title": "Result", "url": "https://example.com"}]}),
    ) as post:
        result = TavilyProvider(api_key="tavily-test").search("test query")
        assert result[0]["provider"] == "tavily"
        assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer tavily-test"

    with patch(
        "providers.web_research.httpx.post",
        return_value=FakeResponse({"data": {"markdown": "# Paper", "metadata": {"title": "Paper"}}}),
    ) as post:
        result = FirecrawlProvider(api_key="firecrawl-test").retrieve("https://example.com")
        assert result["markdown"] == "# Paper"
        assert post.call_args.args[0] == "https://api.firecrawl.dev/v2/scrape"

    print("Web research tools smoke check passed.")


if __name__ == "__main__":
    main()
