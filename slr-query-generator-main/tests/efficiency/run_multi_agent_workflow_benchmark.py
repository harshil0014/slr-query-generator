"""Benchmark the local multi-agent LangGraph orchestration path.

All provider tools are deterministic local replacements. This isolates agent and
workflow overhead; it does not measure remote LLM, search, or retrieval time.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.data_extraction import DataExtractionAgent
from agents.deduplication import DeduplicationAgent
from agents.paper_retrieval import PaperRetrievalAgent
from agents.paper_search import PaperSearchAgent
from agents.planner import PlannerAgent
from agents.query_generation import QueryGenerationAgent
from agents.registry import AgentRegistry
from agents.screening import ScreeningAgent
from agents.validator import ValidatorAgent
from tests.efficiency.agent_timer import benchmark_agent
from tools.registry import ToolRegistry
from workflows.research_workflow import build_research_workflow


class InMemoryWorkflowMemory:
    def persist_update(self, previous: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
        return {**previous, **update}


class TimedAgent:
    """Proxy that records only the agent's own execute time."""

    def __init__(self, agent, timings: dict[str, list[float]]) -> None:
        self._agent = agent
        self._timings = timings
        self.agent_id = agent.agent_id
        self.description = agent.description

    def execute(self, state: dict[str, Any]) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            return self._agent.execute(state)
        finally:
            self._timings[self.agent_id].append((time.perf_counter() - started) * 1000)


def _metrics(samples: list[float]) -> dict[str, float | int]:
    samples = sorted(samples)
    p95_index = min(len(samples) - 1, int(len(samples) * 0.95))
    return {
        "calls": len(samples),
        "mean_ms": round(statistics.fmean(samples), 4),
        "median_ms": round(statistics.median(samples), 4),
        "p95_ms": round(samples[p95_index], 4),
        "max_ms": round(samples[-1], 4),
    }


def build_workflow(timings: dict[str, list[float]]):
    tools = ToolRegistry()
    tools.register("query.generate", lambda topic: {"query": f'(\"{topic}\")', "source": "benchmark"})
    tools.register("query.validate", lambda _: {"valid": True, "errors": []})
    tools.register("search.openalex", lambda query, **_: [{"title": query, "doi": "10.1/example", "url": "https://example.test/paper"}])
    tools.register("web.retrieve.firecrawl", lambda _: {"text": "local benchmark document"})
    tools.register("deduplicate.run", lambda papers: {"papers": papers, "input_count": len(papers), "removed": 0})
    tools.register("screen.run", lambda papers, *_args, **_kwargs: {"papers": [{**paper, "Decision": "KEEP"} for paper in papers], "summary": {"keep": len(papers)}, "engine": "benchmark"})
    tools.register("extract.structured", lambda documents, _topic: {"records": [{"title": doc["title"]} for doc in documents], "failures": []})

    registry = AgentRegistry()
    agents = [
        PlannerAgent(registry), QueryGenerationAgent(tools), PaperSearchAgent(tools),
        PaperRetrievalAgent(tools), DeduplicationAgent(tools), ScreeningAgent(tools),
        DataExtractionAgent(tools), ValidatorAgent(tools),
    ]
    for agent in agents:
        registry.register(TimedAgent(agent, timings))
    return build_research_workflow(InMemoryWorkflowMemory(), registry)


def initial_state() -> dict[str, Any]:
    return {
        "run_id": "efficiency-benchmark",
        "topic": "Explainable AI in Healthcare",
        "preferred_databases": ["openalex"],
        "inclusion_criteria": [], "exclusion_criteria": [],
        "events": [], "errors": [], "artifacts": {},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark the full local multi-agent workflow.")
    parser.add_argument("--iterations", type=int, default=100)
    parser.add_argument("--warmup", type=int, default=10)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    timings: dict[str, list[float]] = defaultdict(list)
    workflow = build_workflow(timings)
    total_metrics = benchmark_agent(lambda _: workflow.invoke(initial_state()), {}, iterations=args.iterations, warmup=args.warmup)
    report = {
        "measured_at": datetime.now(UTC).isoformat(),
        "measurement": "local multi-agent orchestration and agent execution; remote services excluded",
        "workflow_metrics": total_metrics,
        "agent_metrics": {agent_id: _metrics(samples) for agent_id, samples in timings.items()},
    }
    print(json.dumps(report, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Saved report to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
