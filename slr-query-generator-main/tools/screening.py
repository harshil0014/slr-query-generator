"""Adapter that exposes the legacy CSV screener as an autonomous API-backed tool."""

from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

import pandas as pd


GEMINI_API_ENGINE = "gemini_api"


def _criteria_text(criteria: list[str] | None) -> str:
    return "\n".join(str(item).strip() for item in (criteria or []) if str(item).strip())


def _screening_rows(papers: list[dict[str, Any]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, paper in enumerate(papers, start=1):
        title = str(paper.get("title") or paper.get("Title") or "").strip()
        if not title:
            raise ValueError(f"Paper {index} is missing a title.")
        rows.append(
            {
                "Title": title,
                "Abstract": str(paper.get("abstract") or paper.get("Abstract") or ""),
            }
        )
    if not rows:
        raise ValueError("At least one paper is required for screening.")
    return rows


def run_screening(
    papers: list[dict[str, Any]],
    research_question: str,
    *,
    inclusion_criteria: list[str] | None = None,
    exclusion_criteria: list[str] | None = None,
    api_key: str | None = None,
    model: str | None = None,
    max_rows: int | None = None,
) -> dict[str, Any]:
    """Screen normalized papers through the existing pipeline using Gemini's API.

    Temporary CSV files are an implementation detail required by the legacy
    pipeline; no user-visible files are created by this autonomous tool.
    """
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is required for autonomous screening.")
    question = str(research_question or "").strip()
    if not question:
        raise ValueError("A research question is required for screening.")

    rows = _screening_rows(papers)
    # Import lazily: legacy screening dependencies must not affect API startup.
    from bulk_screen import screen_csv

    with TemporaryDirectory(prefix="slr-autonomous-screening-") as directory:
        directory_path = Path(directory)
        input_path = directory_path / "papers.csv"
        output_path = directory_path / "screened.csv"
        pd.DataFrame(rows).to_csv(input_path, index=False)

        options: dict[str, Any] = {
            "csv_path": str(input_path),
            "research_question": question,
            "output_path": str(output_path),
            "mode": GEMINI_API_ENGINE,
            "screening_engine": GEMINI_API_ENGINE,
            "gemini_api_key": api_key,
            "inclusion_criteria": _criteria_text(inclusion_criteria),
            "exclusion_criteria": _criteria_text(exclusion_criteria),
            "max_rows": max_rows,
        }
        if model:
            options["model"] = model
        summary = screen_csv(**options)
        if not output_path.exists():
            raise RuntimeError("Legacy screening completed without producing a result file.")
        screened_papers = pd.read_csv(output_path).fillna("").to_dict(orient="records")

    return {
        "engine": GEMINI_API_ENGINE,
        "summary": summary,
        "papers": screened_papers,
    }


def register_screening_tools(registry) -> None:
    registry.register("screen.run", run_screening)
