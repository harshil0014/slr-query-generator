"""Measure local execution latency for the Query Generation Agent.

This benchmark deliberately replaces the external query provider with a local
deterministic tool, so its result measures agent overhead rather than network
or model-response time.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.query_generation import QueryGenerationAgent
from tests.efficiency.agent_timer import benchmark_agent
from tools.registry import ToolRegistry


def build_agent() -> QueryGenerationAgent:
    tools = ToolRegistry()
    tools.register(
        "query.generate",
        lambda topic: {"query": f'(\"{topic}\")', "source": "efficiency-test"},
    )
    return QueryGenerationAgent(tools)


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark QueryGenerationAgent latency.")
    parser.add_argument("--iterations", type=int, default=1_000)
    parser.add_argument("--warmup", type=int, default=100)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    report = {
        "agent": QueryGenerationAgent.agent_id,
        "measured_at": datetime.now(UTC).isoformat(),
        "measurement": "local agent execution only; external model and network time excluded",
        "metrics": benchmark_agent(
            build_agent().execute,
            {"topic": "Explainable AI in Healthcare"},
            iterations=args.iterations,
            warmup=args.warmup,
        ),
    }
    print(json.dumps(report, indent=2))

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Saved report to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
