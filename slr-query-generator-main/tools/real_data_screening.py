"""Transparent no-LLM first-pass screening for live bibliographic records."""

from __future__ import annotations

import re
from typing import Any


STOP_WORDS = {"about", "after", "between", "from", "into", "paper", "research", "review", "study", "studies", "system", "systems", "that", "the", "this", "with"}


def _terms(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9]{4,}", text.lower()) if word not in STOP_WORDS}


def screen_live_records(
    papers: list[dict[str, Any]],
    topic: str,
    *,
    inclusion_criteria: list[str] | None = None,
    exclusion_criteria: list[str] | None = None,
    **_: Any,
) -> dict[str, Any]:
    """Screen real records using visible lexical evidence and clear reasons.

    It deliberately labels borderline records as MAYBE instead of inventing an
    LLM judgement. The later relevance ranking retains only the requested
    number of records marked KEEP.
    """
    topic_terms = _terms(topic)
    inclusion_terms = _terms(" ".join(inclusion_criteria or []))
    exclusion_phrases = [item.strip().lower() for item in (exclusion_criteria or []) if item.strip()]
    screened: list[dict[str, Any]] = []
    counts = {"keep": 0, "maybe": 0, "reject": 0}

    for paper in papers:
        text = f"{paper.get('title') or paper.get('Title') or ''} {paper.get('abstract') or paper.get('Abstract') or ''}".lower()
        words = _terms(text)
        topic_hits = len(topic_terms & words)
        criterion_hits = len(inclusion_terms & words)
        matched_exclusion = next((phrase for phrase in exclusion_phrases if phrase in text), "")
        updated = dict(paper)
        if matched_exclusion:
            decision, confidence, reason = "REJECT", "High", f"Rejected: matched exclusion criterion '{matched_exclusion}'."
        elif topic_hits >= max(1, min(2, len(topic_terms))):
            confidence = "High" if topic_hits >= 3 or criterion_hits >= 2 else "Medium"
            decision = "KEEP"
            reason = f"Eligible: matched {topic_hits} topic term(s) and {criterion_hits} inclusion-criterion term(s) in title/abstract."
        elif topic_hits:
            decision, confidence, reason = "MAYBE", "Low", "Borderline: partial topic match; requires manual title/abstract review."
        else:
            decision, confidence, reason = "REJECT", "High", "Rejected: title and abstract did not contain sufficient topic evidence."
        counts[decision.lower()] += 1
        updated.update({"Decision": decision, "Confidence": confidence, "Reason": reason})
        screened.append(updated)
    return {"engine": "real_metadata_lexical_screening", "summary": counts, "papers": screened}


def register_real_data_screening_tool(registry) -> None:
    registry.register("screen.run", screen_live_records)
