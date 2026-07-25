"""API-backed web-research providers used only through the Tool Registry."""

from __future__ import annotations

import os
from typing import Any

import httpx

from services.retry import retry


class TavilyProvider:
    provider_id = "tavily"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key

    def search(
        self,
        query: str,
        *,
        limit: int = 5,
        include_domains: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        api_key = self._api_key or os.getenv("TAVILY_API_KEY")
        if not api_key:
            raise RuntimeError("TAVILY_API_KEY is required for Tavily web search.")
        payload: dict[str, Any] = {
            "query": query,
            "search_depth": "basic",
            "max_results": max(1, min(limit, 20)),
        }
        if include_domains:
            payload["include_domains"] = include_domains

        def request() -> dict[str, Any]:
            response = httpx.post(
                "https://api.tavily.com/search",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()

        result = retry(request)
        return [
            {
                "provider": self.provider_id,
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "score": item.get("score"),
            }
            for item in result.get("results", [])
        ]


class FirecrawlProvider:
    provider_id = "firecrawl"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key

    def retrieve(self, url: str) -> dict[str, Any]:
        api_key = self._api_key or os.getenv("FIRECRAWL_API_KEY")
        if not api_key:
            raise RuntimeError("FIRECRAWL_API_KEY is required for Firecrawl retrieval.")

        def request() -> dict[str, Any]:
            response = httpx.post(
                "https://api.firecrawl.dev/v2/scrape",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"url": url, "formats": ["markdown"], "onlyMainContent": True},
                timeout=float(os.getenv("FIRECRAWL_TIMEOUT_SECONDS", "20")),
            )
            response.raise_for_status()
            return response.json()

        # Full-text retrieval is optional enrichment. A single bounded attempt
        # prevents one unreachable publisher page from blocking the workflow.
        payload = retry(request, attempts=1)
        data = payload.get("data") or {}
        return {
            "provider": self.provider_id,
            "url": url,
            "markdown": data.get("markdown", ""),
            "metadata": data.get("metadata", {}),
        }
