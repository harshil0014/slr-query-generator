from __future__ import annotations

from operator import add
from typing import Annotated, Any, TypedDict

from agents.bootstrap import bootstrap_registries
from agents.registry import AgentRegistry, get_agent_registry
from memory.shared_memory import SharedWorkflowMemory


def _merge_artifacts(
    current: dict[str, Any], update: dict[str, Any]
) -> dict[str, Any]:
    return {**current, **update}


class GraphState(TypedDict, total=False):
    run_id: str
    topic: str
    lifecycle: str
    execution_plan: list[str]
    completed_agents: list[str]
    next_agent: str | None
    queries: dict[str, str]
    search_results: list[dict[str, Any]]
    retrieved_documents: list[dict[str, Any]]
    deduplicated_results: list[dict[str, Any]]
    screening_results: list[dict[str, Any]]
    extracted_data: list[dict[str, Any]]
    validation: dict[str, Any]
    artifacts: Annotated[dict[str, Any], _merge_artifacts]
    events: Annotated[list[dict[str, Any]], add]
    errors: Annotated[list[dict[str, str]], add]
    updated_at: str
    inclusion_criteria: list[str]
    exclusion_criteria: list[str]
    preferred_databases: list[str]
    paper_limit: int
    target_included_papers: int
    publication_year_from: int | None
    publication_year_to: int | None


def _next_agent(state: GraphState) -> str | None:
    plan = state.get("execution_plan", [])
    completed = set(state.get("completed_agents", []))
    return next((agent_id for agent_id in plan if agent_id not in completed), None)


def build_research_workflow(memory: SharedWorkflowMemory, registry: AgentRegistry | None = None):
    """Build a registry-driven LangGraph without importing concrete agent implementations."""
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:
        raise RuntimeError("LangGraph is required; install requirements.txt.") from exc

    bootstrap_registries()
    registry = registry or get_agent_registry()
    graph = StateGraph(GraphState)

    def make_node(agent_id: str):
        def node(state: GraphState) -> dict[str, Any]:
            try:
                update = registry.get(agent_id).execute(dict(state))
                completed = list(state.get("completed_agents", []))
                if agent_id not in completed:
                    completed.append(agent_id)
                update["completed_agents"] = completed
                update["next_agent"] = _next_agent({**state, **update})
            except Exception as exc:
                update = {
                    "lifecycle": "FAILED",
                    "errors": [{"agent": agent_id, "message": str(exc)}],
                    "next_agent": None,
                    "events": [{"agent": agent_id, "event": "failed", "message": str(exc)}],
                }
            memory.persist_update(dict(state), update)
            return update
        return node

    for agent_id in registry.ids():
        graph.add_node(agent_id, make_node(agent_id))
    graph.add_edge(START, "planner")

    def route(state: GraphState):
        return state.get("next_agent") or END

    for agent_id in registry.ids():
        graph.add_conditional_edges(agent_id, route)
    return graph.compile()
