from __future__ import annotations

import os

from agents.data_extraction import DataExtractionAgent
from agents.deduplication import DeduplicationAgent
from agents.evidence_synthesis import EvidenceSynthesisAgent
from agents.paper_retrieval import PaperRetrievalAgent
from agents.paper_search import PaperSearchAgent
from agents.planner import PlannerAgent
from agents.quality_assessment import QualityAssessmentAgent
from agents.query_generation import QueryGenerationAgent
from agents.registry import get_agent_registry
from agents.report_generation import ReportGenerationAgent
from agents.screening import ScreeningAgent
from agents.validator import ValidatorAgent
from tools.data_extraction import register_data_extraction_tools
from tools.deduplication import register_deduplication_tools
from tools.evidence_synthesis import register_synthesis_tools
from tools.quality_assessment import register_quality_assessment_tools
from tools.query_tools import register_query_tools
from tools.registry import get_tool_registry
from tools.reporting import register_reporting_tools
from tools.review_exports import register_review_export_tools
from tools.real_data_screening import register_real_data_screening_tool
from tools.screening import register_screening_tools
from tools.scholarly_search import register_scholarly_tools
from tools.web_research import register_web_research_tools


def _register_local_demo_tools(tools) -> None:
    """Register deterministic tools so the complete UI can run without APIs."""
    from tools.reporting import generate_report

    tools.register("query.generate", lambda topic: {"query": f'\"{topic}\"', "source": "local_demo"})
    tools.register("query.validate", lambda query: {"valid": bool(str(query).strip()), "errors": []})
    def local_search(query, *, limit=25, **_):
        count = max(10, min(int(limit), 1000))
        return [{
            "title": f"Local demo study {index} on {query}", "doi": f"10.0000/local-demo-{index}",
            "url": f"https://example.test/local-demo-{index}", "abstract": "A deterministic local demo record.",
            "authors": ["Local Demo"], "publication_year": 2026, "provider": "local_demo",
        } for index in range(1, count + 1)]

    tools.register("search.openalex", local_search)
    tools.register("web.retrieve.firecrawl", lambda url: {"url": url, "markdown": "Local demo evidence document."})
    tools.register("deduplicate.run", lambda papers: {"papers": papers, "input_count": len(papers), "removed": 0})
    tools.register("screen.run", lambda papers, *_args, **_kwargs: {
        "papers": [{**paper, "Decision": "KEEP", "Reason": "Included by local demo."} for paper in papers],
        "summary": {"keep": len(papers), "reject": 0}, "engine": "local_demo",
    })
    tools.register("extract.structured", lambda documents, _topic: {"records": [{
        "title": document.get("title", ""), "objective": "Local workflow demonstration",
        "methodology": "Deterministic fixture", "population_or_context": "Local environment",
        "data_sources": "Built-in fixture", "key_findings": "The workflow completed locally.",
        "limitations": "Not a real literature search.", "relevance_rationale": "Verifies the agent pipeline.",
    } for document in documents], "failures": []})
    tools.register("quality.assess", lambda papers, _topic: {"assessments": [{
        "title": paper.get("title", ""), "methodology_rigor": "Moderate",
        "data_sources_quality": "Moderate", "limitations_acknowledged": "Yes",
        "relevance_to_research": "High", "overall_quality_score": "3", "quality_justification": "Local demo assessment.",
    } for paper in papers], "summary": {"papers_assessed": len(papers), "average_quality_score": 3.0, "high_quality_count": 0, "moderate_quality_count": len(papers), "low_quality_count": 0}})
    tools.register("synthesize.evidence", lambda records, topic, **_: {
        "executive_summary": f"Local demonstration synthesis for {topic}.",
        "key_themes": ["End-to-end orchestration"], "research_gaps": ["Uses local fixture data"],
        "future_work": ["Configure live providers for a real review."],
    })
    tools.register("report.generate", generate_report)
    register_review_export_tools(tools)


def bootstrap_registries() -> None:
    """Register initial agents and tools exactly once at application startup."""
    tools = get_tool_registry()
    if not tools.ids():
        if os.getenv("AUTONOMOUS_LOCAL_MODE", "").lower() in {"1", "true", "yes"}:
            _register_local_demo_tools(tools)
        elif os.getenv("AUTONOMOUS_REAL_DATA_MODE", "").lower() in {"1", "true", "yes"}:
            register_query_tools(tools)
            register_scholarly_tools(tools)
            register_web_research_tools(tools)
            register_deduplication_tools(tools)
            register_real_data_screening_tool(tools)
            register_data_extraction_tools(tools)
            register_quality_assessment_tools(tools)
            register_synthesis_tools(tools)
            register_reporting_tools(tools)
            register_review_export_tools(tools)
        else:
            register_query_tools(tools)
            register_scholarly_tools(tools)
            register_web_research_tools(tools)
            register_deduplication_tools(tools)
            register_screening_tools(tools)
            register_data_extraction_tools(tools)
            register_quality_assessment_tools(tools)
            register_synthesis_tools(tools)
            register_reporting_tools(tools)
            register_review_export_tools(tools)

    agents = get_agent_registry()
    if not agents.ids():
        agents.register(PlannerAgent(agents))
        agents.register(QueryGenerationAgent(tools))
        agents.register(PaperSearchAgent(tools))
        agents.register(PaperRetrievalAgent(tools))
        agents.register(DeduplicationAgent(tools))
        agents.register(ScreeningAgent(tools))
        agents.register(DataExtractionAgent(tools))
        agents.register(QualityAssessmentAgent(tools))
        agents.register(EvidenceSynthesisAgent(tools))
        agents.register(ValidatorAgent(tools))
        agents.register(ReportGenerationAgent(tools))
