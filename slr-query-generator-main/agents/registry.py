from __future__ import annotations

from .base import WorkflowAgent


class AgentRegistry:
    """The only mechanism the workflow uses to discover and execute agents."""

    def __init__(self) -> None:
        self._agents: dict[str, WorkflowAgent] = {}

    def register(self, agent: WorkflowAgent) -> None:
        if agent.agent_id in self._agents:
            raise ValueError(f"Agent already registered: {agent.agent_id}")
        self._agents[agent.agent_id] = agent

    def get(self, agent_id: str) -> WorkflowAgent:
        try:
            return self._agents[agent_id]
        except KeyError as exc:
            raise KeyError(f"Unknown agent: {agent_id}") from exc

    def ids(self) -> tuple[str, ...]:
        return tuple(self._agents)

    def describe(self) -> list[dict[str, str]]:
        return [
            {"id": agent.agent_id, "description": agent.description}
            for agent in self._agents.values()
        ]


_registry = AgentRegistry()


def get_agent_registry() -> AgentRegistry:
    return _registry
