"""Adapter exposing the existing LitSync deduplication logic as an agent tool."""

from __future__ import annotations

from typing import Any

import pandas as pd

from litsync import MAPPED_KEYS, deduplicate


def _as_authors(value: Any) -> str:
    if isinstance(value, list):
        return "; ".join(str(author) for author in value if str(author).strip())
    return str(value or "")


def _lit_sync_row(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "Authors": _as_authors(record.get("authors") or record.get("Authors")),
        "Title": str(record.get("title") or record.get("Title") or ""),
        "Year": record.get("publication_year") or record.get("Year") or "",
        "Source title": str(record.get("source") or record.get("Source title") or record.get("provider") or ""),
        "Cited by": record.get("cited_by") or record.get("Cited by") or "",
        "DOI": str(record.get("doi") or record.get("DOI") or ""),
        "Link": str(record.get("url") or record.get("Link") or ""),
        "Abstract": str(record.get("abstract") or record.get("Abstract") or ""),
    }


def _normalized_record(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": row.get("Title", ""),
        "authors": row.get("Authors", ""),
        "publication_year": row.get("Year", ""),
        "source": row.get("Source title", ""),
        "cited_by": row.get("Cited by", ""),
        "doi": row.get("DOI", ""),
        "url": row.get("Link", ""),
        "abstract": row.get("Abstract", ""),
    }


def deduplicate_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Deduplicate normalized research records using the existing LitSync rules."""
    mapped = [_lit_sync_row(record) for record in records]
    deduplicated, removed = deduplicate(pd.DataFrame(mapped, columns=MAPPED_KEYS))
    papers = [_normalized_record(row) for row in deduplicated.to_dict(orient="records")]
    return {"papers": papers, "removed": removed, "input_count": len(records)}


def register_deduplication_tools(registry) -> None:
    registry.register("deduplicate.run", deduplicate_records)
