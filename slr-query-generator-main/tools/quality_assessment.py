"""Lightweight quality assessment tool using Gemini for scoring included papers."""

from __future__ import annotations

from typing import Any


QUALITY_FIELDS = [
    "methodology_rigor",
    "data_sources_quality",
    "limitations_acknowledged",
    "relevance_to_research",
    "overall_quality_score",
    "quality_justification",
]


def _ask_gemini(prompt: str, *, model: str, api_key: str | None) -> str:
    from gemini_client import ask_gemini

    return ask_gemini(prompt, model=model, api_key=api_key)


def _parse_score(text: str) -> dict[str, Any]:
    """Parse a simple quality assessment response into structured fields."""
    result: dict[str, Any] = {
        "methodology_rigor": "Not assessed",
        "data_sources_quality": "Not assessed",
        "limitations_acknowledged": "Not assessed",
        "relevance_to_research": "Not assessed",
        "overall_quality_score": "Not assessed",
        "quality_justification": "",
    }
    lines = str(text or "").strip().split("\n")
    for line in lines:
        lower = line.strip().lower()
        if lower.startswith("methodology"):
            result["methodology_rigor"] = line.split(":", 1)[-1].strip()
        elif lower.startswith("data sources"):
            result["data_sources_quality"] = line.split(":", 1)[-1].strip()
        elif lower.startswith("limitations"):
            result["limitations_acknowledged"] = line.split(":", 1)[-1].strip()
        elif lower.startswith("relevance"):
            result["relevance_to_research"] = line.split(":", 1)[-1].strip()
        elif lower.startswith("overall score") or lower.startswith("overall_quality"):
            result["overall_quality_score"] = line.split(":", 1)[-1].strip()
        elif lower.startswith("justification") or lower.startswith("quality_justification"):
            result["quality_justification"] = line.split(":", 1)[-1].strip()
    return result


def _quality_prompt(title: str, abstract: str, topic: str) -> str:
    return f"""Assess the methodological quality of this paper for a systematic literature review on: {topic}

Paper title: {title}
Abstract: {abstract[:2000] if abstract else 'No abstract available'}

Rate each dimension as: High / Moderate / Low / Not applicable

Methodology rigor:
Data sources quality:
Limitations acknowledged:
Relevance to research question:
Overall quality score (1-5):
Quality justification (one sentence):

Return only the ratings, no additional text."""


def assess_paper_quality(
    paper: dict[str, Any],
    research_topic: str,
    *,
    model: str = "gemini-2.5-flash",
    api_key: str | None = None,
) -> dict[str, Any]:
    """Score a single paper's quality using Gemini."""
    title = str(paper.get("title") or paper.get("Title") or "")
    abstract = str(paper.get("abstract") or paper.get("Abstract") or paper.get("markdown") or "")
    prompt = _quality_prompt(title, abstract, research_topic)
    try:
        response = _ask_gemini(prompt, model=model, api_key=api_key)
        scores = _parse_score(response)
        scores["title"] = title
        return scores
    except Exception as exc:
        return {
            "title": title,
            "methodology_rigor": "Error",
            "data_sources_quality": "Error",
            "limitations_acknowledged": "Error",
            "relevance_to_research": "Error",
            "overall_quality_score": "Error",
            "quality_justification": f"Assessment failed: {exc}",
        }


def assess_quality_batch(
    papers: list[dict[str, Any]],
    research_topic: str,
    *,
    model: str = "gemini-2.5-flash",
    api_key: str | None = None,
) -> dict[str, Any]:
    """Assess quality of multiple included papers."""
    assessments: list[dict[str, Any]] = []
    for paper in papers:
        assessment = assess_paper_quality(paper, research_topic, model=model, api_key=api_key)
        assessments.append(assessment)

    avg_scores = []
    for a in assessments:
        score_str = str(a.get("overall_quality_score", "")).strip()
        try:
            avg_scores.append(float(score_str.split("/")[0].strip()))
        except (ValueError, TypeError):
            avg_scores.append(0.0)

    summary = {
        "papers_assessed": len(assessments),
        "average_quality_score": sum(avg_scores) / len(avg_scores) if avg_scores else 0.0,
        "high_quality_count": sum(1 for s in avg_scores if s >= 4),
        "moderate_quality_count": sum(1 for s in avg_scores if 2 <= s < 4),
        "low_quality_count": sum(1 for s in avg_scores if 0 < s < 2),
        "unassessed_count": sum(1 for s in avg_scores if s == 0),
    }

    return {"assessments": assessments, "summary": summary}


def register_quality_assessment_tools(registry) -> None:
    registry.register("quality.assess", assess_quality_batch)
