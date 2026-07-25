from __future__ import annotations

from agents.bootstrap import bootstrap_registries
from agents.paper_search import PaperSearchAgent
from agents.planner import PlannerAgent
from agents.query_generation import QueryGenerationAgent
from agents.registry import AgentRegistry, get_agent_registry
from agents.validator import ValidatorAgent
from memory.shared_memory import SharedWorkflowMemory
from state.research_workflow_state import ResearchWorkflowState, WorkflowLifecycle
from tools.registry import ToolRegistry, get_tool_registry
from workflows.research_workflow import build_research_workflow


class FakeRepository:
    def __init__(self) -> None:
        self.states = {}
        self.events = []

    def create(self, state):
        self.states[state.run_id] = state.graph_state()

    def get(self, run_id):
        return self.states.get(run_id)

    def save_state(self, state):
        self.states[state["run_id"]] = state

    def append_event(self, run_id, event):
        self.events.append((run_id, event))


def _registry_with_four_working_agents():
    tools = ToolRegistry()
    tools.register("query.generate", lambda topic: {"query": '"' + topic + '"', "source": "test"})
    tools.register("query.validate", lambda query: {"valid": bool(query), "errors": [], "query": query})
    tools.register("search.openalex", lambda query, **_: [{"title": "A study", "provider": "openalex"}])

    registry = AgentRegistry()
    registry.register(PlannerAgent(registry))
    registry.register(QueryGenerationAgent(tools))
    registry.register(PaperSearchAgent(tools))
    registry.register(ValidatorAgent(tools))
    return registry


def test_bootstrap_registries_registers_full_pipeline_agents_and_tools():
    agent_registry = get_agent_registry()
    agent_registry._agents.clear()
    tool_registry = get_tool_registry()
    tool_registry._tools.clear()

    bootstrap_registries()

    assert "paper_retrieval" in agent_registry.ids()
    assert "deduplication" in agent_registry.ids()
    assert "deduplicate.run" in tool_registry.ids()
    assert "web.retrieve.firecrawl" in tool_registry.ids()


def test_registry_driven_langgraph_executes_four_phase_one_agents():
    repository = FakeRepository()
    state = ResearchWorkflowState.new(topic="Explainable AI in Healthcare")
    repository.create(state)

    graph = build_research_workflow(SharedWorkflowMemory(repository), _registry_with_four_working_agents())
    final_state = graph.invoke(state.graph_state())

    assert final_state["lifecycle"] == WorkflowLifecycle.COMPLETED.value
    assert final_state["completed_agents"] == ["planner", "query_generation", "paper_search", "validator"]
    assert final_state["queries"]["google_scholar"] == '"Explainable AI in Healthcare"'
    assert len(final_state["search_results"]) == 1
    assert final_state["validation"]["valid"] is True
    assert repository.get(state.run_id)["lifecycle"] == WorkflowLifecycle.COMPLETED.value
    assert len(repository.events) == 4
