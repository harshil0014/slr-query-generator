"""Registry adapters for web-search and content-retrieval providers."""

from providers.web_research import FirecrawlProvider, TavilyProvider


def register_web_research_tools(registry) -> None:
    registry.register("web.search.tavily", TavilyProvider().search)
    registry.register("web.retrieve.firecrawl", FirecrawlProvider().retrieve)
