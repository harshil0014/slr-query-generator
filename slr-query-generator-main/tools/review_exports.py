"""CSV exports for transparent autonomous-review decisions."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


BIBLIOGRAPHIC_COLUMNS = ["Authors", "Title", "Year", "Source title", "Cited by", "DOI", "Link", "Abstract"]
DECISION_COLUMNS = [
    "Paper_ID", "Decision", "Reason", "Confidence", "Required_Evidence",
    "Paper_Contribution", "processing_engine", "screening_strategy", "batch_number",
]


def _value(paper: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = paper.get(key)
        if value not in (None, ""):
            if isinstance(value, list):
                return "; ".join(str(item) for item in value)
            return str(value)
    return ""


def _row(paper: dict[str, Any], index: int, state: dict[str, Any], contributions: dict[str, str]) -> dict[str, str]:
    title = _value(paper, "Title", "title")
    screening = (state.get("artifacts") or {}).get("screening") or {}
    required_evidence = "; ".join(str(item) for item in state.get("inclusion_criteria", []) if str(item).strip())
    return {
        "Authors": _value(paper, "Authors", "authors"),
        "Title": title,
        "Year": _value(paper, "Year", "publication_year"),
        "Source title": _value(paper, "Source title", "source", "provider"),
        "Cited by": _value(paper, "Cited by", "cited_by"),
        "DOI": _value(paper, "DOI", "doi"),
        "Link": _value(paper, "Link", "url"),
        "Abstract": _value(paper, "Abstract", "abstract"),
        "Paper_ID": f"P{index:04d}",
        "Decision": _value(paper, "Decision", "decision") or "UNSCREENED",
        "Reason": _value(paper, "Reason", "reason") or "No screening reason recorded.",
        "Confidence": _value(paper, "Confidence", "confidence") or "Not scored",
        "Required_Evidence": required_evidence or "Topic relevance and screening criteria",
        "Paper_Contribution": contributions.get(title.casefold(), "Not extracted"),
        "processing_engine": str(screening.get("engine") or "unknown"),
        "screening_strategy": "criteria_screening_then_relevance_ranking",
        "batch_number": str((index - 1) // 100 + 1),
    }


def _write(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=BIBLIOGRAPHIC_COLUMNS + DECISION_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def export_review_csvs(state: dict[str, Any]) -> dict[str, dict[str, str | int]]:
    """Write all candidates, included studies, and excluded studies as CSV files."""
    run_id = str(state.get("run_id") or "review")
    contributions = {
        str(record.get("title") or "").casefold(): str(record.get("key_findings") or record.get("relevance_rationale") or "Not extracted")
        for record in state.get("extracted_data", [])
    }
    rows = [_row(paper, index, state, contributions) for index, paper in enumerate(state.get("screening_results", []), start=1)]
    included = [row for row in rows if row["Decision"].upper() == "KEEP"]
    excluded = [row for row in rows if row["Decision"].upper() != "KEEP"]
    directory = Path("outputs") / "autonomous_reviews" / run_id
    files = {
        "all_screened": ("all_screened_papers.csv", rows),
        "included": ("final_included_papers.csv", included),
        "excluded": ("excluded_papers.csv", excluded),
    }
    exports: dict[str, dict[str, str | int]] = {}
    for key, (filename, export_rows) in files.items():
        path = directory / filename
        _write(path, export_rows)
        exports[key] = {
            "filename": filename,
            "row_count": len(export_rows),
            "download_url": f"/outputs/autonomous_reviews/{run_id}/{filename}",
        }
    return exports


def register_review_export_tools(registry) -> None:
    registry.register("review.export_csvs", export_review_csvs)
