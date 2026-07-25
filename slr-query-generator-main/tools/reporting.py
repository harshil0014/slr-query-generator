"""Deterministic Markdown report generation for the autonomous demo workflow."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _bullet_items(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- Not specified"


def generate_report(state: dict[str, Any]) -> dict[str, str]:
    """Create a readable SLR report without introducing another model dependency."""
    screening = state.get("screening_results", [])
    included = [
        row for row in screening
        if str(row.get("Decision") or row.get("decision") or "").upper() == "KEEP"
    ]
    extracted = state.get("extracted_data", [])
    query = (state.get("queries") or {}).get("google_scholar", "")
    assessments = state.get("quality_assessments", [])
    quality_summary = state.get("quality_summary", {})
    synthesis = state.get("synthesis", {})
    lines = [
        f"# Systematic Literature Review: {state.get('topic', 'Untitled Review')}",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Research Scope",
        state.get("topic", ""),
        "",
        "### Inclusion Criteria",
        _bullet_items(state.get("inclusion_criteria", [])),
        "",
        "### Exclusion Criteria",
        _bullet_items(state.get("exclusion_criteria", [])),
        "",
        "## Search Strategy",
        f"Boolean query: `{query}`" if query else "Boolean query was not available.",
        f"Papers retrieved: {len(state.get('search_results', []))}",
        f"Papers screened: {len(screening)}",
        f"Studies included: {len(included)}",
        "",
        "## Included Studies",
    ]
    if included:
        for index, paper in enumerate(included, start=1):
            lines.append(f"{index}. **{paper.get('Title') or paper.get('title') or 'Untitled'}**")
            if paper.get("Reason") or paper.get("reason"):
                lines.append(f"   - Screening rationale: {paper.get('Reason') or paper.get('reason')}")
    else:
        lines.append("No studies met the current screening criteria.")

    lines.extend(["", "## Quality Assessment"])
    if assessments:
        lines.append(f"### Summary")
        lines.append(f"- Papers assessed: {quality_summary.get('papers_assessed', 0)}")
        lines.append(f"- Average quality score: {quality_summary.get('average_quality_score', 'N/A')}/5")
        lines.append(f"- High quality (4-5): {quality_summary.get('high_quality_count', 0)}")
        lines.append(f"- Moderate quality (2-4): {quality_summary.get('moderate_quality_count', 0)}")
        lines.append(f"- Low quality (1-2): {quality_summary.get('low_quality_count', 0)}")
        lines.append("")
        lines.append("### Per-Study Scores")
        for index, assessment in enumerate(assessments, start=1):
            lines.extend([
                f"{index}. **{assessment.get('title', 'Untitled')}**",
                f"   - Methodology rigor: {assessment.get('methodology_rigor', 'N/A')}",
                f"   - Data sources: {assessment.get('data_sources_quality', 'N/A')}",
                f"   - Limitations acknowledged: {assessment.get('limitations_acknowledged', 'N/A')}",
                f"   - Relevance: {assessment.get('relevance_to_research', 'N/A')}",
                f"   - Overall score: {assessment.get('overall_quality_score', 'N/A')}",
                f"   - Justification: {assessment.get('quality_justification', 'N/A')}",
            ])
    else:
        lines.append("Quality assessment was not performed.")

    lines.extend(["", "## Evidence Synthesis"])
    exec_summary = (synthesis or {}).get("executive_summary", "")
    if exec_summary:
        lines.extend([
            "### Executive Summary",
            exec_summary,
        ])
    themes = (synthesis or {}).get("key_themes", [])
    if themes:
        lines.extend(["", "### Key Themes"])
        for theme in themes:
            lines.append(f"- {theme}")
    gaps = (synthesis or {}).get("research_gaps", [])
    if gaps:
        lines.extend(["", "### Research Gaps"])
        for gap in gaps:
            lines.append(f"- {gap}")
    future = (synthesis or {}).get("future_work", [])
    if future:
        lines.extend(["", "### Future Work"])
        for item in future:
            lines.append(f"- {item}")
    if not exec_summary and not themes:
        lines.append("Evidence synthesis was not performed.")

    lines.extend(["", "## Extracted Evidence"])
    if extracted:
        for index, record in enumerate(extracted, start=1):
            lines.extend([
                f"### {index}. {record.get('title') or 'Untitled'}",
                f"- Objective: {record.get('objective') or 'Not reported'}",
                f"- Methodology: {record.get('methodology') or 'Not reported'}",
                f"- Population/Context: {record.get('population_or_context') or 'Not reported'}",
                f"- Data sources: {record.get('data_sources') or 'Not reported'}",
                f"- Key findings: {record.get('key_findings') or 'Not reported'}",
                f"- Limitations: {record.get('limitations') or 'Not reported'}",
                f"- Relevance: {record.get('relevance_rationale') or 'Not reported'}",
            ])
    else:
        lines.append("No structured evidence was extracted.")

    lines.extend([
        "",
        "## Demo Notes",
        "This report was generated autonomously by the multi-agent SLR research assistant. ",
        "Workflow: Planner -> Query Generation -> Search -> Retrieval -> Deduplication -> ",
        "Screening -> Data Extraction -> Quality Assessment -> Evidence Synthesis -> Report Generation.",
    ])
    return {"markdown": "\n".join(lines) + "\n"}


def register_reporting_tools(registry) -> None:
    registry.register("report.generate", generate_report)
