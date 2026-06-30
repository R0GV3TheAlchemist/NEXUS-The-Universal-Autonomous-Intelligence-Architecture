"""
GAIA Benchmark — Minimal Pipeline Latency
Measures end-to-end time for the v0.1 pipeline.
Target: < 2 seconds per claim on a standard laptop.

Usage:
    python benchmarks/pipeline_latency.py
    python benchmarks/pipeline_latency.py --runs 100
"""

import sys
import time
import json
import statistics
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from examples.minimal_pipeline import run_pipeline


SAMPLE_INPUTS = [
    "Solar panels reduce energy costs over time",
    "Supply chain disruptions increase manufacturing costs",
    "Network nodes with higher trust produce more reliable consensus",
    "Adversarial validation improves epistemic accuracy",
    "Renewable energy expansion reduces grid emissions",
]


def run_benchmark(n_runs: int = 20) -> dict:
    timings = []

    for i in range(n_runs):
        text = SAMPLE_INPUTS[i % len(SAMPLE_INPUTS)]
        start = time.perf_counter()
        run_pipeline(text)
        elapsed = time.perf_counter() - start
        timings.append(elapsed)

    results = {
        "benchmark":   "pipeline_latency",
        "gaia_version": "0.1.0",
        "runs":         n_runs,
        "mean_ms":      round(statistics.mean(timings) * 1000, 2),
        "median_ms":    round(statistics.median(timings) * 1000, 2),
        "p95_ms":       round(sorted(timings)[int(n_runs * 0.95)] * 1000, 2),
        "max_ms":       round(max(timings) * 1000, 2),
        "min_ms":       round(min(timings) * 1000, 2),
        "target_ms":    2000,
        "passed":       statistics.mean(timings) * 1000 < 2000
    }
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=20)
    args = parser.parse_args()

    print(f"\n⏱  GAIA Benchmark — Pipeline Latency ({args.runs} runs)")
    results = run_benchmark(args.runs)
    print(json.dumps(results, indent=2))
    status = "✅ PASSED" if results["passed"] else "❌ FAILED"
    print(f"\n{status} — mean latency: {results['mean_ms']}ms (target: {results['target_ms']}ms)\n")
