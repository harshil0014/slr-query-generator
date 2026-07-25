"""Gemini-backed structured evidence extraction tool."""

from __future__ import annotations

import json
from typing import Any

EXTRACTION_FIELDS = (
    "objective",
    "methodology",
    "population_or_context",
    "data_sources",
    "key_findings",
    "limitations",
    "relevance_rationale",
)
MAX_DOCUMENT_CHARS = 24_000


def _ask_gemini(prompt: str, *, model: str, api_key: str | None) -> str:
    # Keep optional legacy client dependencies out of application startup.
    from gemini_client import ask_gemini

    return ask_gemini(prompt, model=model, api_key=api_key)


def _parse_json_object(response: str) -> dict[str, Any]:
    text = str(response or "").strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("Gemini did not return a JSON object.")
    payload = json.loads(text[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("Gemini extraction response must be a JSON object.")
    return payload


def _prompt(document: dict[str, Any], research_topic: str) -> str:
    content = str(document.get("markdown") or document.get("content") or "")[:MAX_DOCUMENT_CHARS]
    return f"""You are extracting evidence for a systematic literature review.
Research topic: {research_topic}
Paper title: {document.get('title', '')}
DOI: {document.get('doi', '')}

Return exactly one JSON object with these string fields:
{", ".join(EXTRACTION_FIELDS)}.
Use an empty string when the paper does not provide a field. Do not add markdown or extra keys.

Paper content:
{content}
"""


def extract_structured_data(
    documents: list[dict[str, Any]],
    research_topic: str,
    *,
    model: str = "gemini-2.5-flash",
    api_key: str | None = None,
) -> dict[str, Any]:
    """Extract comparable evidence records from retrieved paper content."""
    records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for document in documents:
        title = str(document.get("title") or "")
        try:
            extracted = _parse_json_object(
                _ask_gemini(_prompt(document, research_topic), model=model, api_key=api_key)
            )
            records.append(
                {
                    "title": title,
                    "doi": str(document.get("doi") or ""),
                    **{field: str(extracted.get(field) or "") for field in EXTRACTION_FIELDS},
                }
            )
        except Exception as exc:
            failures.append({"title": title, "message": str(exc)})
    return {"records": records, "failures": failures}


def register_data_extraction_tools(registry) -> None:
    registry.register("extract.structured", extract_structured_data)
