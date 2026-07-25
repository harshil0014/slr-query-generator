"""Lightweight evidence synthesis tool using a single Gemini call."""

from __future__ import annotations

from typing import Any


def _ask_gemini(prompt: str, *, model: str, api_key: str | None) -> str:
    from gemini_client import ask_gemini

    return ask_gemini(prompt, model=model, api_key=api_key)


def _build_synthesis_prompt(
    topic: str,
    extracted_data: list[dict[str, Any]],
    quality_summary: dict[str, Any] | None,
) -> str:
    records_text = ""
    for i, record in enumerate(extracted_data, 1):
        records_text += f"""
Study {i}:
- Title: {record.get('title', 'N/A')}
- Objective: {record.get('objective', 'N/A')}
- Methodology: {record.get('methodology', 'N/A')}
- Population/Context: {record.get('population_or_context', 'N/A')}
- Data Sources: {record.get('data_sources', 'N/A')}
- Key Findings: {record.get('key_findings', 'N/A')}
- Limitations: {record.get('limitations', 'N/A')}
- Relevance: {record.get('relevance_rationale', 'N/A')}
"""

    quality_context = ""
    if quality_summary:
        quality_context = f"""
Quality Assessment Context:
- Papers assessed: {quality_summary.get('papers_assessed', 0)}
- Average quality score: {quality_summary.get('average_quality_score', 'N/A')}/5
- High quality: {quality_summary.get('high_quality_count', 0)}
- Moderate quality: {quality_summary.get('moderate_quality_count', 0)}
- Low quality: {quality_summary.get('low_quality_count', 0)}
"""

    return f"""You are an expert systematic literature review analyst. Synthesize the following extracted evidence from studies on: {topic}

{records_text}
{quality_context}

Generate a structured synthesis with the following sections. Be concise and evidence-based.

EXECUTIVE SUMMARY:
(2-3 sentences summarising the overall state of evidence)

KEY THEMES:
(List 3-5 major themes that emerge across the studies. For each theme, state the theme name and a brief explanation)

RESEARCH GAPS:
(List 2-4 gaps or limitations in the current body of evidence)

FUTURE WORK:
(2-3 recommendations for future research directions)

Return each section with its heading exactly as shown above. Use plain text, no markdown formatting."""


def synthesize_evidence(
    extracted_data: list[dict[str, Any]],
    research_topic: str,
    quality_summary: dict[str, Any] | None = None,
    *,
    model: str = "gemini-2.5-flash",
    api_key: str | None = None,
) -> dict[str, Any]:
    """Generate an evidence synthesis from extracted study data using a single Gemini call."""
    if not extracted_data:
        return {
            "executive_summary": "No studies were available for synthesis.",
            "key_themes": ["No themes identified."],
            "research_gaps": ["Insufficient data to identify gaps."],
            "future_work": ["Additional primary studies are required."],
        }

    prompt = _build_synthesis_prompt(research_topic, extracted_data, quality_summary)
    raw = _ask_gemini(prompt, model=model, api_key=api_key).strip()

    sections = {
        "executive_summary": "",
        "key_themes": [],
        "research_gaps": [],
        "future_work": [],
    }

    current_section = None
    for line in raw.split("\n"):
        stripped = line.strip()
        if stripped.upper().startswith("EXECUTIVE SUMMARY"):
            current_section = "executive_summary"
            continue
        elif stripped.upper().startswith("KEY THEMES"):
            current_section = "key_themes"
            continue
        elif stripped.upper().startswith("RESEARCH GAPS"):
            current_section = "research_gaps"
            continue
        elif stripped.upper().startswith("FUTURE WORK"):
            current_section = "future_work"
            continue

        if current_section == "executive_summary":
            sections["executive_summary"] += stripped + " "
        elif current_section in ("key_themes", "research_gaps", "future_work"):
            if stripped.startswith("-") or stripped.startswith("*"):
                sections[current_section].append(stripped.lstrip("-*").strip())
            elif stripped and not stripped.startswith("#"):
                sections[current_section].append(stripped)

    sections["executive_summary"] = sections["executive_summary"].strip()

    return sections


def register_synthesis_tools(registry) -> None:
    registry.register("synthesize.evidence", synthesize_evidence)
