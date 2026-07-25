from __future__ import annotations

from typing import Any

import httpx

from services.retry import retry


class OpenAlexProvider:
    provider_id = "openalex"

    def search(self, query: str, *, from_year: int | None = None, to_year: int | None = None, limit: int = 25) -> list[dict[str, Any]]:
        requested = max(1, min(int(limit), 1000))
        params: dict[str, Any] = {"search": query, "per-page": min(requested, 200)}
        if from_year or to_year:
            start = from_year or 1900
            end = to_year or 2100
            params["filter"] = f"from_publication_date:{start}-01-01,to_publication_date:{end}-12-31"

        records: list[dict[str, Any]] = []
        for page in range(1, (requested + 199) // 200 + 1):
            page_params = {**params, "page": page, "per-page": min(200, requested - len(records))}

            def request() -> dict[str, Any]:
                response = httpx.get("https://api.openalex.org/works", params=page_params, timeout=20.0)
                response.raise_for_status()
                return response.json()

            payload = retry(request)
            results = payload.get("results", [])
            records.extend(self._normalize(item) for item in results)
            if len(results) < page_params["per-page"]:
                break
        return records[:requested]

    @staticmethod
    def _normalize(item: dict[str, Any]) -> dict[str, Any]:
        doi = item.get("doi") or ""
        return {
            "provider": "openalex",
            "provider_id": item.get("id", ""),
            "title": item.get("display_name", ""),
            "doi": doi.replace("https://doi.org/", ""),
            "publication_year": item.get("publication_year"),
            "abstract": "",
            "url": item.get("doi") or item.get("id", ""),
            "authors": [author.get("author", {}).get("display_name", "") for author in item.get("authorships", [])],
        }


class SemanticScholarProvider:
    provider_id = "semantic_scholar"

    def search(self, query: str, *, limit: int = 25, **_: Any) -> list[dict[str, Any]]:
        def request() -> dict[str, Any]:
            response = httpx.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={"query": query, "limit": min(limit, 100), "fields": "title,abstract,year,authors,externalIds,url"},
                timeout=20.0,
            )
            response.raise_for_status()
            return response.json()

        payload = retry(request)
        return [
            {
                "provider": self.provider_id,
                "provider_id": item.get("paperId", ""),
                "title": item.get("title", ""),
                "doi": (item.get("externalIds") or {}).get("DOI", ""),
                "publication_year": item.get("year"),
                "abstract": item.get("abstract") or "",
                "url": item.get("url", ""),
                "authors": [author.get("name", "") for author in item.get("authors", [])],
            }
            for item in payload.get("data", [])
        ]


class CrossrefProvider:
    provider_id = "crossref"

    def search(self, query: str, *, from_year: int | None = None, to_year: int | None = None, limit: int = 25) -> list[dict[str, Any]]:
        filters = []
        if from_year:
            filters.append(f"from-pub-date:{from_year}-01-01")
        if to_year:
            filters.append(f"until-pub-date:{to_year}-12-31")

        def request() -> dict[str, Any]:
            params: dict[str, Any] = {"query": query, "rows": min(limit, 100)}
            if filters:
                params["filter"] = ",".join(filters)
            response = httpx.get("https://api.crossref.org/works", params=params, timeout=20.0)
            response.raise_for_status()
            return response.json()

        payload = retry(request)
        return [
            {
                "provider": self.provider_id,
                "provider_id": item.get("DOI", ""),
                "title": (item.get("title") or [""])[0],
                "doi": item.get("DOI", ""),
                "publication_year": ((item.get("published") or {}).get("date-parts") or [[None]])[0][0],
                "abstract": item.get("abstract") or "",
                "url": item.get("URL", ""),
                "authors": [" ".join(filter(None, [author.get("given"), author.get("family")])) for author in item.get("author", [])],
            }
            for item in payload.get("message", {}).get("items", [])
        ]


class ArxivProvider:
    provider_id = "arxiv"

    def search(self, query: str, *, limit: int = 25, **_: Any) -> list[dict[str, Any]]:
        # arXiv exposes Atom XML; parsing belongs behind this provider boundary in Phase 2.
        raise NotImplementedError("arXiv retrieval will be enabled in Phase 2; select openalex, crossref, or semantic_scholar today.")
