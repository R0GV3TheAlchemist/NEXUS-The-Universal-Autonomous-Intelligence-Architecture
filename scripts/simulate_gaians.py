#!/usr/bin/env python3
"""
scripts/simulate_gaians.py

GAIAN Concurrent Simulation Harness
Tracks: Issue #265

Simulates N GAIAN agents running concurrently, each executing a
configurable number of Emrys-style cycles, and reports:
  - Individual and collective Φ (integrated information)
  - Routing flag distribution across all agents
  - Phase-lock status distribution
  - Agents in active_inference / classical_prior / buffer
  - Wall-clock time for the full simulation

Usage:
    python scripts/simulate_gaians.py --agents 100
    python scripts/simulate_gaians.py --agents 1000 --cycles 10 --output results/sim_1000.json
    python scripts/simulate_gaians.py --agents 100 --scenario somnus

Scenarios:
    nominal   — standard operation (default)
    somnus    — all agents enter NREM sleep simultaneously (C158)
    surge     — 30% of agents have degraded fidelity (stress test)
    cold_boot — all agents start from cold-start state
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import math
import os
import random
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("gaia.simulate")


# ── Synthetic Emrys cycle (mirrors emrys_cycle.py contract) ───────────────────

@dataclass
class SimCycleResult:
    agent_id:    str
    cycle:       int
    phi:         float
    fidelity:    float
    phase_offset_ms: float
    routing_flag: str
    temp_K:      float
    elapsed_ms:  float


def _synthetic_phi(scenario: str, agent_index: int) -> float:
    """Generate scenario-appropriate Φ values."""
    if scenario == "somnus":
        # NREM: low Φ, mostly below wake threshold (0.15)
        return max(0.0, random.gauss(0.10, 0.04))
    elif scenario == "surge":
        # 30% of agents degraded
        if agent_index % 10 < 3:
            return max(0.0, random.gauss(0.15, 0.06))
        return max(0.0, random.gauss(0.42, 0.12))
    elif scenario == "cold_boot":
        # Cold-boot: Φ starts low and rises over cycles
        return max(0.0, random.gauss(0.22, 0.08))
    else:  # nominal
        return max(0.0, random.gauss(0.45, 0.12))


def _synthetic_fidelity(scenario: str, agent_index: int) -> float:
    if scenario == "somnus":
        return max(0.0, min(1.0, random.gauss(0.55, 0.10)))
    elif scenario == "surge" and agent_index % 10 < 3:
        return max(0.0, min(1.0, random.gauss(0.38, 0.08)))
    else:
        return max(0.0, min(1.0, random.gauss(0.76, 0.08)))


def _routing_flag(fidelity: float, phi: float, phase_offset: float,
                  scenario: str) -> str:
    if scenario == "somnus":
        return "sleep_scan"
    if fidelity < 0.45 or phase_offset > 8.0:
        return "buffer"
    if fidelity >= 0.72 and phi > 0.3 and phase_offset <= 2.0:
        return "active_inference"
    return "classical_prior"


async def _run_agent(
    agent_index: int,
    n_cycles: int,
    scenario: str,
    results: list,
) -> float:
    """Simulate one GAIAN agent for n_cycles. Returns mean Φ."""
    agent_id = f"agent-{agent_index:05d}"
    phi_sum = 0.0

    for cycle in range(n_cycles):
        t0 = time.monotonic()

        # Simulate 40 Hz cycle execution time (2-18 ms)
        sim_latency = random.uniform(0.002, 0.018)
        await asyncio.sleep(sim_latency)

        phi         = _synthetic_phi(scenario, agent_index)
        fidelity    = _synthetic_fidelity(scenario, agent_index)
        phase_offset = abs(random.gauss(1.2, 2.0))
        temp_K      = 310.0 + random.gauss(0, 0.5)
        flag        = _routing_flag(fidelity, phi, phase_offset, scenario)
        elapsed_ms  = (time.monotonic() - t0) * 1000

        phi_sum += phi
        results.append(SimCycleResult(
            agent_id=agent_id,
            cycle=cycle,
            phi=round(phi, 4),
            fidelity=round(fidelity, 4),
            phase_offset_ms=round(phase_offset, 3),
            routing_flag=flag,
            temp_K=round(temp_K, 2),
            elapsed_ms=round(elapsed_ms, 2),
        ))

    return phi_sum / n_cycles if n_cycles else 0.0


# ── Collective Φ aggregation ───────────────────────────────────────────────────

def _collective_phi(agent_phis: List[float]) -> float:
    """
    Aggregate individual Φ values into a collective Φ estimate.

    Method: geometric mean of non-zero Φ values.
    Rationale: Φ is multiplicative in information integration;
    geometric mean reflects the collective coherence floor.
    Zero-Φ agents (buffer/sleep) are excluded from the aggregate.
    """
    non_zero = [p for p in agent_phis if p > 0]
    if not non_zero:
        return 0.0
    log_sum = sum(math.log(p) for p in non_zero)
    return math.exp(log_sum / len(non_zero))


# ── Report ─────────────────────────────────────────────────────────────────────

def _build_report(
    scenario: str,
    n_agents: int,
    n_cycles: int,
    agent_phis: List[float],
    all_results: List[SimCycleResult],
    wall_time_s: float,
) -> dict:
    routing_counts: dict[str, int] = {}
    for r in all_results:
        routing_counts[r.routing_flag] = routing_counts.get(r.routing_flag, 0) + 1

    total = len(all_results)
    routing_pct = {
        k: round(v / total * 100, 1)
        for k, v in routing_counts.items()
    }

    phi_values = [r.phi for r in all_results]
    fid_values = [r.fidelity for r in all_results]

    return {
        "simulation_id":   str(uuid.uuid4()),
        "timestamp_utc":   datetime.now(timezone.utc).isoformat(),
        "scenario":        scenario,
        "agents":          n_agents,
        "cycles_per_agent":n_cycles,
        "total_cycles":    total,
        "wall_time_s":     round(wall_time_s, 2),
        "collective_phi":  round(_collective_phi(agent_phis), 4),
        "phi": {
            "mean":   round(sum(phi_values) / len(phi_values), 4),
            "min":    round(min(phi_values), 4),
            "max":    round(max(phi_values), 4),
        },
        "fidelity": {
            "mean":   round(sum(fid_values) / len(fid_values), 4),
            "min":    round(min(fid_values), 4),
            "max":    round(max(fid_values), 4),
        },
        "routing_distribution": routing_pct,
        "agents_active_inference":  routing_counts.get("active_inference", 0),
        "agents_classical_prior":   routing_counts.get("classical_prior", 0),
        "agents_buffer":            routing_counts.get("buffer", 0),
        "agents_sleep_scan":        routing_counts.get("sleep_scan", 0),
        "acceptance": {
            "buffer_rate_below_5pct": routing_pct.get("buffer", 0) < 5.0,
            "collective_phi_above_0_3": _collective_phi(agent_phis) > 0.3,
            "note": "buffer_rate_below_5pct is EP-03 acceptance criterion",
        },
    }


# ── Main ───────────────────────────────────────────────────────────────────────

async def main(n_agents: int, n_cycles: int, scenario: str, output: str | None):
    log.info("GAIA Simulation: %d agents × %d cycles — scenario: %s",
             n_agents, n_cycles, scenario)

    all_results: list[SimCycleResult] = []
    t0 = time.monotonic()

    # Run all agents concurrently
    agent_phis = await asyncio.gather(*[
        _run_agent(i, n_cycles, scenario, all_results)
        for i in range(n_agents)
    ])

    wall_time = time.monotonic() - t0

    report = _build_report(
        scenario, n_agents, n_cycles,
        list(agent_phis), all_results, wall_time,
    )

    # Print summary
    print()
    print("━" * 60)
    print(f"  GAIA SIMULATION REPORT — {scenario.upper()}")
    print("━" * 60)
    print(f"  Agents:             {n_agents}")
    print(f"  Cycles/agent:       {n_cycles}")
    print(f"  Total cycles:       {report['total_cycles']}")
    print(f"  Wall time:          {report['wall_time_s']}s")
    print()
    print(f"  Collective Φ:       {report['collective_phi']}")
    print(f"  Mean Φ:             {report['phi']['mean']}")
    print(f"  Mean Fidelity:      {report['fidelity']['mean']}")
    print()
    print("  Routing distribution:")
    for flag, pct in report["routing_distribution"].items():
        bar = "█" * int(pct / 2)
        print(f"    {flag:<20} {pct:5.1f}%  {bar}")
    print()
    print(f"  EP-03 (buffer < 5%):        {'✅ PASS' if report['acceptance']['buffer_rate_below_5pct'] else '❌ FAIL'}")
    print(f"  Collective Φ > 0.3:         {'✅ PASS' if report['acceptance']['collective_phi_above_0_3'] else '❌ FAIL'}")
    print("━" * 60)

    if output:
        os.makedirs(os.path.dirname(output) or ".", exist_ok=True)
        with open(output, "w") as f:
            json.dump(report, f, indent=2)
        log.info("Report written → %s", output)
    else:
        print()
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="GAIA GAIAN Concurrent Simulation Harness"
    )
    parser.add_argument("-n", "--agents",   type=int, default=100,
                        help="Number of concurrent GAIAN agents (default: 100)")
    parser.add_argument("-c", "--cycles",   type=int, default=5,
                        help="Cycles per agent (default: 5)")
    parser.add_argument("-s", "--scenario", type=str, default="nominal",
                        choices=["nominal", "somnus", "surge", "cold_boot"],
                        help="Simulation scenario (default: nominal)")
    parser.add_argument("-o", "--output",   type=str, default=None,
                        help="Output JSON path (default: stdout)")
    args = parser.parse_args()

    asyncio.run(main(args.agents, args.cycles, args.scenario, args.output))
