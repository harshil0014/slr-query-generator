"""Lightweight smoke tests for the autonomous SLR multi-agent workflow.

These tests verify:
- All agents are registered and discoverable.
- Planner sequence includes all expected agents.
- Tool registry is complete.
- State model includes all required fields.
- Report generation includes QA and synthesis content.
- Workflow graph can be built without error.

No network connectivity is required.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from agents.bootstrap import bootstrap_registries
from agents.registry import get_agent_registry
from memory.shared_memory import SharedWorkflowMemory
from repositories.workflow_repository import ResearchWorkflowRepository
from state.research_workflow_state import ResearchWorkflowState, WorkflowLifecycle
from tools.registry import get_tool_registry


# =============================================================================
# Fixtures
# =============================================================================


class _InMemoryRepository(ResearchWorkflowRepository):
    """Lightweight in-memory store for smoke tests — no Supabase dependency."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    def create(self, state: ResearchWorkflowState) -> ResearchWorkflowState:
        raw = state.graph_state()
        raw["created_at"] = (
            raw["created_at"].isoformat()
            if hasattr(raw["created_at"], "isoformat")
            else raw["created_at"]
        )
        raw["updated_at"] = (
            raw["updated_at"].isoformat()
            if hasattr(raw["updated_at"], "isoformat")
            else raw["updated_at"]
        )
        self._store[state.run_id] = raw
        return state

    def get(self, run_id: str) -> dict[str, Any] | None:
        return self._store.get(run_id)

    def update(self, run_id: str, state: dict[str, Any]) -> None:
        self._store[run_id] = {**self._store.get(run_id, {}), **state}


@pytest.fixture(scope="module")
def repo() -> _InMemoryRepository:
    return _InMemoryRepository()


@pytest.fixture(scope="module")
def memory(repo: _InMemoryRepository) -> SharedWorkflowMemory:
    return SharedWorkflowMemory(repo)


# =============================================================================
# Constants
# =============================================================================

EXPECTED_AGENTS = [
    "planner",
    "query_generation",
    "paper_search",
    "paper_retrieval",
    "deduplication",
    "screening",
    "data_extraction",
    "quality_assessment",
    "evidence_synthesis",
    "validator",
    "report_generation",
]

EXPECTED_TOOLS = [
    "query.generate",
    "query.validate",
    "search.openalex",
    "web.retrieve.firecrawl",
    "deduplicate.run",
    "screen.run",
    "extract.structured",
    "quality.assess",
    "synthesize.evidence",
    "report.generate",
]


# =============================================================================
# Test: Agent Registration
# =============================================================================


class TestAgentRegistration:
    """Verify every expected agent is registered and discoverable."""

    def setup_method(self) -> None:
        bootstrap_registries()

    def test_all_expected_agents_are_registered(self) -> None:
        registry = get_agent_registry()
        registered = set(registry.ids())
        for agent_id in EXPECTED_AGENTS:
            assert agent_id in registered, f"Missing agent: {agent_id}"

    def test_agent_count_matches_expectations(self) -> None:
        registry = get_agent_registry()
        assert len(registry.ids()) == len(EXPECTED_AGENTS), (
            f"Expected {len(EXPECTED_AGENTS)} agents, got {len(registry.ids())}"
        )

    def test_each_agent_has_description(self) -> None:
        registry = get_agent_registry()
        for desc in registry.describe():
            assert desc["id"] in EXPECTED_AGENTS, f"Unexpected agent: {desc['id']}"
            assert desc["description"], f"Agent {desc['id']} has empty description"


# =============================================================================
# Test: Planner Sequence
# =============================================================================


class TestPlannerSequence:
    """Verify the planner produces the correct execution plan."""

    def setup_method(self) -> None:
        bootstrap_registries()

    def _run_planner(self) -> dict[str, Any]:
        from agents.planner import PlannerAgent

        registry = get_agent_registry()
        planner = PlannerAgent(registry)
        state = {
            "topic": "AI in healthcare",
            "inclusion_criteria": ["peer-reviewed"],
            "exclusion_criteria": ["opinion"],
        }
        return planner.execute(state)

    def test_planner_includes_all_expected_agents(self) -> None:
        result = self._run_planner()
        plan = result.get("execution_plan", [])
        # Planner itself is the orchestrator, not a step in the plan
        expected_steps = [a for a in EXPECTED_AGENTS if a != "planner"]
        for agent_id in expected_steps:
            assert agent_id in plan, f"Planner missing: {agent_id}"

    def test_planner_sequence_is_correct(self) -> None:
        result = self._run_planner()
        plan = result.get("execution_plan", [])
        assert plan.index("query_generation") < plan.index("paper_search")
        assert plan.index("screening") < plan.index("data_extraction")
        assert plan.index("data_extraction") < plan.index("quality_assessment")
        assert plan.index("quality_assessment") < plan.index("evidence_synthesis")
        assert plan.index("evidence_synthesis") < plan.index("report_generation")

    def test_planner_outputs_valid_workflow_state(self) -> None:
        result = self._run_planner()
        assert result["lifecycle"] == WorkflowLifecycle.PLANNING.value
        assert "planner" in result.get("completed_agents", [])
        assert result.get("next_agent") == result["execution_plan"][0]
        assert len(result.get("events", [])) > 0


# =============================================================================
# Test: Tool Registration
# =============================================================================


class TestToolRegistry:
    """Verify every expected tool is registered and callable."""

    def setup_method(self) -> None:
        bootstrap_registries()

    def test_all_expected_tools_are_registered(self) -> None:
        registry = get_tool_registry()
        registered = set(registry.ids())
        for tool_id in EXPECTED_TOOLS:
            assert tool_id in registered, f"Missing tool: {tool_id}"

    def test_tool_count_matches_expectations(self) -> None:
        registry = get_tool_registry()
        assert len(registry.ids()) >= len(EXPECTED_TOOLS), (
            f"Expected at least {len(EXPECTED_TOOLS)} tools, got {len(registry.ids())}"
        )

    def test_registered_tools_are_callable(self) -> None:
        registry = get_tool_registry()
        for tool_id in registry.ids():
            tool = registry.get(tool_id)
            assert callable(tool), f"Tool {tool_id} is not callable"


# =============================================================================
# Test: State Model
# =============================================================================


class TestWorkflowStateModel:
    """Verify the state model includes all required fields for the full workflow."""

    REQUIRED_FIELDS = [
        "run_id",
        "topic",
        "inclusion_criteria",
        "exclusion_criteria",
        "lifecycle",
        "execution_plan",
        "completed_agents",
        "next_agent",
        "queries",
        "search_results",
        "retrieved_documents",
        "deduplicated_results",
        "screening_results",
        "extracted_data",
        "quality_assessments",
        "quality_summary",
        "synthesis",
        "validation",
        "artifacts",
        "events",
        "errors",
    ]

    def test_state_has_all_required_fields(self) -> None:
        state = ResearchWorkflowState.new(topic="test topic")
        for field in self.REQUIRED_FIELDS:
            assert hasattr(state, field), f"State missing field: {field}"

    def test_initial_lifecycle_is_created(self) -> None:
        state = ResearchWorkflowState.new(topic="test topic")
        assert state.lifecycle == WorkflowLifecycle.CREATED

    def test_quality_assessment_fields_are_present(self) -> None:
        state = ResearchWorkflowState.new(topic="test topic")
        assert state.quality_assessments == []
        assert state.quality_summary == {}
        assert state.synthesis == {}

    def test_workflow_lifecycle_values(self) -> None:
        expected_states = [
            "CREATED", "PLANNING", "QUERY_GENERATION", "SEARCHING",
            "PAPER_RETRIEVAL", "DEDUPLICATION", "SCREENING",
            "DATA_EXTRACTION", "QUALITY_ASSESSMENT", "SYNTHESIS",
            "REPORT_GENERATION", "COMPLETED", "FAILED", "PAUSED",
        ]
        for state_name in expected_states:
            assert hasattr(WorkflowLifecycle, state_name), f"Missing lifecycle: {state_name}"

    def test_graph_state_is_json_serializable(self) -> None:
        from datetime import datetime, timezone

        state = ResearchWorkflowState.new(topic="test topic")
        raw = state.graph_state()
        raw["created_at"] = datetime.now(timezone.utc).isoformat()
        raw["updated_at"] = datetime.now(timezone.utc).isoformat()
        dumped = json.dumps(raw, default=str)
        assert isinstance(dumped, str)
        loaded = json.loads(dumped)
        assert loaded["topic"] == "test topic"


# =============================================================================
# Test: Report Generation
# =============================================================================


class TestReportGeneration:
    """Verify the report tool produces output including QA and synthesis."""

    def setup_method(self) -> None:
        bootstrap_registries()

    def test_report_includes_quality_assessment_section(self) -> None:
        from tools.reporting import generate_report

        state = _make_sample_state_with_qa()
        result = generate_report(state)
        markdown = result.get("markdown", "")
        assert "Quality Assessment" in markdown

    def test_report_includes_evidence_synthesis_section(self) -> None:
        from tools.reporting import generate_report

        state = _make_sample_state_with_synthesis()
        result = generate_report(state)
        markdown = result.get("markdown", "")
        assert "Evidence Synthesis" in markdown

    def test_report_includes_executive_summary(self) -> None:
        from tools.reporting import generate_report

        state = _make_sample_state_with_synthesis()
        result = generate_report(state)
        markdown = result.get("markdown", "")
        assert "Executive Summary" in markdown

    def test_report_includes_key_themes(self) -> None:
        from tools.reporting import generate_report

        state = _make_sample_state_with_synthesis()
        result = generate_report(state)
        markdown = result.get("markdown", "")
        assert "Key Themes" in markdown

    def test_report_includes_research_gaps(self) -> None:
        from tools.reporting import generate_report

        state = _make_sample_state_with_synthesis()
        result = generate_report(state)
        markdown = result.get("markdown", "")
        assert "Research Gaps" in markdown

    def test_report_includes_extracted_evidence(self) -> None:
        from tools.reporting import generate_report

        state = _make_sample_state_with_extraction()
        result = generate_report(state)
        markdown = result.get("markdown", "")
        assert "Extracted Evidence" in markdown

    def test_report_includes_demo_notes(self) -> None:
        from tools.reporting import generate_report

        state = _make_sample_state_with_qa()
        result = generate_report(state)
        markdown = result.get("markdown", "")
        assert "Demo Notes" in markdown


# =============================================================================
# Test: Workflow Graph Construction
# =============================================================================


class TestWorkflowGraph:
    """Verify the LangGraph workflow can be built without error."""

    def setup_method(self) -> None:
        bootstrap_registries()

    def test_graph_builds_without_error(self, memory: SharedWorkflowMemory) -> None:
        from workflows.research_workflow import build_research_workflow

        graph = build_research_workflow(memory)
        assert graph is not None

    def test_graph_has_all_agent_nodes(self, memory: SharedWorkflowMemory) -> None:
        from workflows.research_workflow import build_research_workflow

        graph = build_research_workflow(memory)
        # LangGraph stores nodes in graph.nodes
        nodes = {name for name in graph.nodes.keys()}
        for agent_id in EXPECTED_AGENTS:
            assert agent_id in nodes, f"Graph missing node: {agent_id}"

    def test_graph_is_valid_compiled_graph(self, memory: SharedWorkflowMemory) -> None:
        from workflows.research_workflow import build_research_workflow

        graph = build_research_workflow(memory)
        # CompiledStateGraph: verify it compiles, has expected nodes, and is invocable
        assert graph is not None, "Graph should compile without error"
        nodes = list(graph.nodes.keys())
        assert "planner" in nodes, "Graph missing planner entry node"
        assert len(nodes) >= len(EXPECTED_AGENTS), (
            f"Graph expected at least {len(EXPECTED_AGENTS)} nodes, got {len(nodes)}"
        )
        # Verify all agent nodes exist in the graph
        for agent_id in EXPECTED_AGENTS:
            assert agent_id in nodes, f"Graph missing agent node: {agent_id}"
        # Verify graph has compiled runnable attribute
        assert hasattr(graph, "invoke"), "Compiled graph must expose invoke method"


# =============================================================================
# Helper: Sample state builders
# =============================================================================


def _make_sample_state_with_qa() -> dict[str, Any]:
    return {
        "topic": "AI in Healthcare",
        "inclusion_criteria": ["peer-reviewed"],
        "exclusion_criteria": ["opinion"],
        "queries": {"google_scholar": "AI healthcare systematic review"},
        "search_results": [{"title": "Sample Study", "abstract": "This is a sample abstract."}],
        "screening_results": [
            {"Title": "Sample Study", "Decision": "KEEP", "Reason": "Relevant"},
            {"Title": "Other Study", "Decision": "REJECT", "Reason": "Out of scope"},
        ],
        "quality_assessments": [
            {
                "title": "Sample Study",
                "methodology_rigor": "High",
                "data_sources_quality": "High",
                "limitations_acknowledged": "Moderate",
                "relevance_to_research": "High",
                "overall_quality_score": "4.0/5",
                "quality_justification": "Well-designed study with robust methodology.",
            }
        ],
        "quality_summary": {
            "papers_assessed": 1,
            "average_quality_score": 4.0,
            "high_quality_count": 1,
            "moderate_quality_count": 0,
            "low_quality_count": 0,
        },
        "extracted_data": [],
        "synthesis": {},
        "artifacts": {},
        "events": [],
        "errors": [],
    }


def _make_sample_state_with_synthesis() -> dict[str, Any]:
    return {
        "topic": "AI in Healthcare",
        "inclusion_criteria": ["peer-reviewed"],
        "exclusion_criteria": ["opinion"],
        "queries": {"google_scholar": "AI healthcare systematic review"},
        "search_results": [{"title": "Sample Study", "abstract": "Sample abstract."}],
        "screening_results": [
            {"Title": "Sample Study", "Decision": "KEEP", "Reason": "Relevant"},
        ],
        "extracted_data": [
            {
                "title": "Sample Study",
                "objective": "To evaluate AI in healthcare",
                "methodology": "Systematic review",
                "population_or_context": "Healthcare providers",
                "data_sources": "PubMed, Scopus",
                "key_findings": "AI improves diagnostic accuracy",
                "limitations": "Small sample size",
                "relevance_rationale": "Directly addresses research question",
            }
        ],
        "quality_assessments": [],
        "quality_summary": {},
        "synthesis": {
            "executive_summary": (
                "The reviewed literature demonstrates that AI technologies "
                "are increasingly being adopted in healthcare settings."
            ),
            "key_themes": [
                "AI improves diagnostic accuracy in radiology",
                "Machine learning models enhance patient outcome prediction",
            ],
            "research_gaps": [
                "Limited real-world validation studies",
                "Lack of standardized evaluation frameworks",
            ],
            "future_work": [
                "Conduct large-scale prospective validation studies",
                "Develop standardized benchmarks for clinical AI systems",
            ],
        },
        "artifacts": {},
        "events": [],
        "errors": [],
    }


def _make_sample_state_with_extraction() -> dict[str, Any]:
    return {
        "topic": "AI in Healthcare",
        "inclusion_criteria": ["peer-reviewed"],
        "exclusion_criteria": ["opinion"],
        "queries": {"google_scholar": "AI healthcare systematic review"},
        "search_results": [{"title": "Sample Study", "abstract": "Sample abstract."}],
        "screening_results": [
            {"Title": "Sample Study", "Decision": "KEEP", "Reason": "Relevant"},
        ],
        "extracted_data": [
            {
                "title": "Sample Study",
                "objective": "To evaluate AI in healthcare",
                "methodology": "Systematic review",
                "population_or_context": "Healthcare providers",
                "data_sources": "PubMed, Scopus",
                "key_findings": "AI improves diagnostic accuracy",
                "limitations": "Small sample size",
                "relevance_rationale": "Directly addresses research question",
            }
        ],
        "quality_assessments": [],
        "quality_summary": {},
        "synthesis": {},
        "artifacts": {},
        "events": [],
        "errors": [],
    }
