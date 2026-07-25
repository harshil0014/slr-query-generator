"""Small dependency-free helpers for timing workflow agents."""

from __future__ import annotations

import statistics
import time
from collections.abc import Callable
from typing import Any


def benchmark_agent(
    execute: Callable[[dict[str, Any]], dict[str, Any]],
    state: dict[str, Any],
    *,
    iterations: int = 100,
    warmup: int = 10,
) -> dict[str, float | int]:
    """Run an agent repeatedly and return latency metrics in milliseconds."""
    if iterations < 1:
        raise ValueError("iterations must be at least 1")
    if warmup < 0:
        raise ValueError("warmup cannot be negative")

    for _ in range(warmup):
        execute(state)

    timings_ms: list[float] = []
    for _ in range(iterations):
        started = time.perf_counter()
        execute(state)
        timings_ms.append((time.perf_counter() - started) * 1000)

    timings_ms.sort()
    p95_index = min(len(timings_ms) - 1, int(len(timings_ms) * 0.95))
    return {
        "iterations": iterations,
        "warmup_iterations": warmup,
        "min_ms": round(timings_ms[0], 4),
        "mean_ms": round(statistics.fmean(timings_ms), 4),
        "median_ms": round(statistics.median(timings_ms), 4),
        "p95_ms": round(timings_ms[p95_index], 4),
        "max_ms": round(timings_ms[-1], 4),
        "throughput_per_second": round(iterations / (sum(timings_ms) / 1000), 2),
    }
