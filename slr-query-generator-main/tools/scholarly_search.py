from __future__ import annotations

from typing import Any

from providers.scholarly import ArxivProvider, CrossrefProvider, OpenAlexProvider, SemanticScholarProvider


def register_scholarly_tools(registry) -> None:
    registry.register("search.openalex", OpenAlexProvider().search)
    registry.register("search.semantic_scholar", SemanticScholarProvider().search)
    registry.register("search.crossref", CrossrefProvider().search)
    registry.register("search.arxiv", ArxivProvider().search)


def search_registered_providers(registry, providers: list[str], query: str, **kwargs: Any) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for provider in providers:
        tool_id = f"search.{provider.strip().lower()}"
        try:
            records.extend(registry.get(tool_id)(query, **kwargs))
        except (KeyError, NotImplementedError, RuntimeError, ValueError) as exc:
            failures.append({"provider": provider, "message": str(exc)})
        except Exception as exc:
            failures.append({"provider": provider, "message": str(exc)})
    if not records and failures:
        raise RuntimeError(f"All scholarly providers failed: {failures}")
    return records
