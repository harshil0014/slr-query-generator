# Agent efficiency tests

This folder contains repeatable latency benchmarks for individual agents and
the full multi-agent workflow. All included benchmarks use local deterministic
tools, isolating orchestration and Python-side overhead from LLM and network
latency.

Install the project dependencies once before running the multi-agent benchmark:

```powershell
python -m pip install -r requirements.txt
```

Run it from the project root:

```powershell
python tests/efficiency/run_query_generation_benchmark.py --iterations 1000 --warmup 100 --output outputs/efficiency/query_generation.json
```

The JSON report includes minimum, mean, median, p95, maximum latency (all in
milliseconds), and throughput per second. To benchmark another agent, create a
similar runner that builds that agent with deterministic local dependencies and
passes its `execute` method to `benchmark_agent`.

## Full multi-agent workflow

This runs planner, query generation, search, retrieval, deduplication,
screening, data extraction, and validation through the LangGraph workflow:

```powershell
python tests/efficiency/run_multi_agent_workflow_benchmark.py --iterations 100 --warmup 10 --output outputs/efficiency/multi_agent_workflow.json
```

`workflow_metrics` is end-to-end time for one workflow. `agent_metrics` breaks
that time down by each agent, making bottlenecks easy to identify.
