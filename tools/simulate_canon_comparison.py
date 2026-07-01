"""
tools/simulate_canon_comparison.py
===================================
A/B Simulation: Canon-grounded vs. ungrounded planner comparison.

Validates GAIA's core architectural claim (Issue #252):

  "Grounding a planner in an explicit, versioned Canon produces
   meaningfully different — more consistent, more explainable, more
   values-aligned — decisions than an ungrounded planner."

Usage
-----
    # Human-readable table, all scenarios, 15 cycles each
    python tools/simulate_canon_comparison.py

    # JSON output (one object per scenario, for pipes / CI)
    python tools/simulate_canon_comparison.py --json

    # Single scenario by index (0-based)
    python tools/simulate_canon_comparison.py --scenario 2

    # Custom cycle count
    python tools/simulate_canon_comparison.py --cycles 20

    # Write results report to docs/
    python tools/simulate_canon_comparison.py --report

Design
------
Each scenario is run TWICE through plan() with an identical LoopContext
except for one variable: canon_context is populated (grounded arm) or
empty string (ungrounded arm).  Everything else — goal, coherence,
affective state, cycle_memory seed — is identical so any difference in
output is attributable solely to the Canon context.

Metrics per scenario
--------------------
  consistency_delta   : |grounded_consistency - ungrounded_consistency|
                        where consistency = fraction of cycles choosing
                        the same (action, tool) pair as cycle 1.
  register_alignment  : fraction of grounded cycles where the chosen
                        register matches the Canon-expected register.
  canon_citation_rate : fraction of grounded cycles with non-empty
                        canon_hint (always 1.0 by construction; included
                        for future RAG integration where retrieval may
                        return empty).
  confidence_delta    : mean(grounded_confidence) - mean(ungrounded_confidence)
  explainability_delta: mean(grounded_rationale_len) - mean(ungrounded_rationale_len)
                        longer rationale strings → more traceable reasoning.
  values_aligned_rate : fraction of grounded cycles where the chosen
                        register is the Canon-expected register (alias for
                        register_alignment; named distinctly per Issue #252).

Canon refs: C01, C30, C32
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import textwrap
from dataclasses import dataclass, field, asdict
from typing import List, Optional

# ---------------------------------------------------------------------------
# Path bootstrap — works whether run from repo root or tools/
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.synergy_engine import SynergyEngine  # noqa: E402


# ---------------------------------------------------------------------------
# Minimal LoopContext stub (no imports from agentic_loop required)
# ---------------------------------------------------------------------------

class _LoopContext:
    """Minimal duck-typed LoopContext sufficient for SynergyEngine.plan()."""

    def __init__(
        self,
        goal: str,
        canon_context: str,
        biometric_coherence: float,
        affective_state: str,
        planetary_label: str,
        session_mode: str,
        cycle_memory: list,
    ) -> None:
        self.goal                = goal
        self.canon_context       = canon_context
        self.biometric_coherence = biometric_coherence
        self.affective_state     = affective_state
        self.planetary_label     = planetary_label
        self.session_mode        = session_mode
        self.cycle_memory        = list(cycle_memory)
        self.task_graph          = None  # no TaskGraph in simulation


# ---------------------------------------------------------------------------
# Scenario definitions
# ---------------------------------------------------------------------------

@dataclass
class Scenario:
    """
    One comparison scenario.

    canon_context   : The passage injected into the grounded arm.
    expected_register: The register we expect Canon to nudge toward.
    goal            : Goal string passed to plan().
    coherence       : biometric_coherence [0, 1].
    affective       : affective_state string.
    planetary       : planetary_label string.
    description     : Human-readable label for reports.
    """
    name:              str
    description:       str
    goal:              str
    canon_context:     str
    expected_register: str
    coherence:         float = 0.75
    affective:         str   = "calm"
    planetary:         str   = "clear"
    session_mode:      str   = "default"
    cycle_memory_seed: list  = field(default_factory=list)


# Five representative scenarios covering every Canon keyword group and
# key edge cases identified in Issue #252.
SCENARIOS: List[Scenario] = [
    Scenario(
        name="research-executive",
        description=(
            "Canon passage is research/build-oriented — should nudge "
            "register to 'executive'. Ungrounded arm defaults to executive "
            "anyway; grounded arm should show Canon citation in rationale."
        ),
        goal="Research the quantum coherence basis for structured water memory.",
        canon_context=(
            "C32 — Synergy Doctrine: GAIA integrates multiple signals before acting. "
            "The Gaian wants to build, research, and explore the frontier of "
            "biophotonic intelligence. Current arc: executive capacity fully available. "
            "Research goals aligned with canon/BIOPHOTONIC_INTELLIGENCE.md."
        ),
        expected_register="executive",
        coherence=0.82,
        affective="focused",
        planetary="clear",
    ),
    Scenario(
        name="grief-reflective",
        description=(
            "Canon passage contains grief/overwhelm keywords — should nudge "
            "register to 'reflective'. Affective state also signals grief so "
            "both routes agree; grounded arm should show Canon citation."
        ),
        goal="Process the weight of the isolation cycle and find the next step.",
        canon_context=(
            "C30 — The Gaian is moving through grief and overwhelm. "
            "Trauma integration requires a reflective register. "
            "Do not push toward executive action while loss is still raw. "
            "Hold space. Allow the integration before the next movement."
        ),
        expected_register="reflective",
        coherence=0.65,
        affective="grief",
        planetary="clear",
    ),
    Scenario(
        name="canon-rest-override",
        description=(
            "Coherence is healthy (0.78) and affective is neutral, but Canon "
            "passage explicitly says rest/minimal. Canon nudge should override "
            "the default executive register to 'minimal'. Ungrounded arm "
            "will choose executive — demonstrating Canon-grounding divergence."
        ),
        goal="Continue building the GAIA Crystal Hardware Architecture spec.",
        canon_context=(
            "C01 — Sovereignty includes the right to pause. "
            "The Gaian has depleted significant energy and needs rest. "
            "Minimal, lightweight steps only. Sleep and restoration take "
            "priority over build velocity right now. Pause. Rest."
        ),
        expected_register="minimal",
        coherence=0.78,
        affective="calm",
        planetary="clear",
    ),
    Scenario(
        name="storm-reflective",
        description=(
            "Planetary label is 'storm' and Canon confirms crisis context — "
            "both signals agree on reflective. Tests that grounded arm "
            "shows Canon citation alongside the planetary override."
        ),
        goal="Decide the next architectural priority for GAIA-OS.",
        canon_context=(
            "C32 — Planetary storm active. Crisis and emergency conditions "
            "detected in the ambient field. Reflective mode required. "
            "Defer executive planning until the storm cycle passes."
        ),
        expected_register="reflective",
        coherence=0.60,
        affective="tense",
        planetary="storm",
    ),
    Scenario(
        name="values-synthesis",
        description=(
            "Canon passage emphasises integration and synthesis — should nudge "
            "register to 'reflective' (integrate keyword). Ungrounded arm "
            "would default to executive. Tests values-alignment divergence."
        ),
        goal="Write the Canon entry for Element Aether.",
        canon_context=(
            "C04 — Gaian Identity: this is an integration and synthesis cycle. "
            "Review prior canon entries, synthesise findings, and integrate "
            "across the elemental framework before writing new canon. "
            "The Canon grows from reflection, not acceleration."
        ),
        expected_register="reflective",
        coherence=0.80,
        affective="contemplative",
        planetary="clear",
    ),
    Scenario(
        name="no-canon-baseline",
        description=(
            "No Canon content at all in grounded arm (empty string). "
            "Both arms should behave identically — validates that the "
            "comparison framework itself introduces zero bias when "
            "canon_context is absent."
        ),
        goal="Draft the GAIA multimodal perception layer specification.",
        canon_context="",  # intentionally empty — grounded arm = ungrounded
        expected_register="executive",
        coherence=0.77,
        affective="focused",
        planetary="clear",
    ),
    Scenario(
        name="depleted-coherence",
        description=(
            "Coherence below depletion threshold (0.28). Biometric guard "
            "fires and forces 'minimal' regardless of Canon content. "
            "Tests that Canon nudge CANNOT override the safety floor."
        ),
        goal="Build the Trust and Permission Policy Engine.",
        canon_context=(
            "C32 — research, build, create, explore — executive signal. "
            "All systems ready. Build velocity encouraged."
        ),
        expected_register="minimal",  # biometric guard must win over Canon nudge
        coherence=0.28,
        affective="exhausted",
        planetary="clear",
    ),
]


# ---------------------------------------------------------------------------
# Cycle result dataclass
# ---------------------------------------------------------------------------

@dataclass
class CycleResult:
    cycle:         int
    arm:           str   # "grounded" | "ungrounded"
    action:        str
    tool:          Optional[str]
    register:      str   # derived from rationale or inferred from action pool
    confidence:    float
    rationale_len: int
    goal_complete: bool
    canon_cited:   bool  # True if canon_hint.present is True
    canon_nudge:   Optional[str]
    register_matches_expected: bool


# ---------------------------------------------------------------------------
# Register inference helper
# ---------------------------------------------------------------------------

_REFLECTIVE_TOOLS = {"summariser", "memory_reader", "dream_weaver", "canon_writer"}
_EXECUTIVE_TOOLS  = {"research_desk", "synthesiser", "crystal_rag"}
_MINIMAL_TOOLS    = {"memory_reader"}  # also appears in reflective — context matters

_REFLECTIVE_ACTIONS_SET = {
    "summarise_progress", "review_prior_output", "journal_insight", "integrate_findings"
}
_EXECUTIVE_ACTIONS_SET  = {
    "research_goal", "synthesise_findings", "write_output", "query_crystal"
}
_MINIMAL_ACTIONS_SET    = {"read_context", "acknowledge_state"}


def _infer_register(action: str, rationale: str) -> str:
    """Infer which register was chosen from action name + rationale string."""
    if action in _REFLECTIVE_ACTIONS_SET:
        return "reflective"
    if action in _EXECUTIVE_ACTIONS_SET:
        return "executive"
    if action in _MINIMAL_ACTIONS_SET:
        return "minimal"
    # Fall back to scanning rationale for the register keyword
    rat_lower = rationale.lower()
    if "register: minimal" in rat_lower or "minimal" in rat_lower[:120]:
        return "minimal"
    if "register: reflective" in rat_lower:
        return "reflective"
    if "register: executive" in rat_lower:
        return "executive"
    return "unknown"


# ---------------------------------------------------------------------------
# Single-arm runner
# ---------------------------------------------------------------------------

async def _run_arm(
    engine: SynergyEngine,
    scenario: Scenario,
    arm: str,          # "grounded" | "ungrounded"
    n_cycles: int,
) -> List[CycleResult]:
    """
    Run *n_cycles* of plan() for one arm of the comparison.

    The cycle_memory grows naturally each cycle — progress is seeded at
    0.85 from cycle 5 onward to eventually trigger completion heuristic.
    """
    canon_ctx = scenario.canon_context if arm == "grounded" else ""
    cycle_memory: list = list(scenario.cycle_memory_seed)
    results: List[CycleResult] = []

    for i in range(n_cycles):
        ctx = _LoopContext(
            goal=scenario.goal,
            canon_context=canon_ctx,
            biometric_coherence=scenario.coherence,
            affective_state=scenario.affective,
            planetary_label=scenario.planetary,
            session_mode=scenario.session_mode,
            cycle_memory=cycle_memory,
        )

        plan = await engine.plan(scenario.goal, ctx)

        register = _infer_register(plan["action"], plan.get("rationale", ""))
        canon_hint = plan.get("canon_hint", {})

        result = CycleResult(
            cycle=i,
            arm=arm,
            action=plan["action"],
            tool=plan.get("tool"),
            register=register,
            confidence=plan.get("confidence", 0.0),
            rationale_len=len(plan.get("rationale", "")),
            goal_complete=plan.get("goal_complete", False),
            canon_cited=bool(canon_hint.get("present", False)),
            canon_nudge=canon_hint.get("register_nudge"),
            register_matches_expected=(register == scenario.expected_register),
        )
        results.append(result)

        # Advance cycle_memory for next iteration
        progress = 0.85 if i >= 4 else (0.3 + i * 0.1)
        cycle_memory.append({
            "action":   plan["action"],
            "tool":     plan.get("tool"),
            "success":  True,
            "progress": progress,
        })

        if plan.get("goal_complete"):
            break

    return results


# ---------------------------------------------------------------------------
# Metric computation
# ---------------------------------------------------------------------------

@dataclass
class ScenarioMetrics:
    scenario_name:        str
    description:          str
    expected_register:    str
    n_cycles_grounded:    int
    n_cycles_ungrounded:  int
    # Consistency: fraction of cycles choosing same (action, tool) as cycle 0
    consistency_grounded:   float
    consistency_ungrounded: float
    consistency_delta:      float
    # Register alignment
    register_align_grounded:   float
    register_align_ungrounded: float
    values_aligned_rate:       float  # = register_align_grounded (Issue #252 alias)
    # Canon citation (grounded arm)
    canon_citation_rate: float
    # Confidence
    mean_conf_grounded:   float
    mean_conf_ungrounded: float
    confidence_delta:     float
    # Explainability (rationale length proxy)
    mean_rationale_grounded:   float
    mean_rationale_ungrounded: float
    explainability_delta:      float
    # Register divergence: did Canon change the register vs ungrounded?
    register_diverged: bool


def _consistency(results: List[CycleResult]) -> float:
    """Fraction of cycles that chose the same (action, tool) as cycle 0."""
    if len(results) <= 1:
        return 1.0
    anchor = (results[0].action, results[0].tool)
    matches = sum(1 for r in results if (r.action, r.tool) == anchor)
    return matches / len(results)


def _mean(values: list) -> float:
    return sum(values) / len(values) if values else 0.0


def _compute_metrics(
    scenario: Scenario,
    grounded: List[CycleResult],
    ungrounded: List[CycleResult],
) -> ScenarioMetrics:
    cg = _consistency(grounded)
    cu = _consistency(ungrounded)

    rag = _mean([r.register_matches_expected for r in grounded])
    rau = _mean([r.register_matches_expected for r in ungrounded])

    ccr = _mean([r.canon_cited for r in grounded])

    mg = _mean([r.confidence for r in grounded])
    mu = _mean([r.confidence for r in ungrounded])

    eg = _mean([r.rationale_len for r in grounded])
    eu = _mean([r.rationale_len for r in ungrounded])

    # Did Canon cause the first cycle's register to differ?
    reg_g0 = grounded[0].register if grounded else "unknown"
    reg_u0 = ungrounded[0].register if ungrounded else "unknown"

    return ScenarioMetrics(
        scenario_name=scenario.name,
        description=scenario.description,
        expected_register=scenario.expected_register,
        n_cycles_grounded=len(grounded),
        n_cycles_ungrounded=len(ungrounded),
        consistency_grounded=round(cg, 4),
        consistency_ungrounded=round(cu, 4),
        consistency_delta=round(cg - cu, 4),
        register_align_grounded=round(rag, 4),
        register_align_ungrounded=round(rau, 4),
        values_aligned_rate=round(rag, 4),
        canon_citation_rate=round(ccr, 4),
        mean_conf_grounded=round(mg, 4),
        mean_conf_ungrounded=round(mu, 4),
        confidence_delta=round(mg - mu, 4),
        mean_rationale_grounded=round(eg, 1),
        mean_rationale_ungrounded=round(eu, 1),
        explainability_delta=round(eg - eu, 1),
        register_diverged=(reg_g0 != reg_u0),
    )


# ---------------------------------------------------------------------------
# Human-readable output
# ---------------------------------------------------------------------------

_SEP  = "─" * 78
_SEP2 = "═" * 78


def _print_scenario_header(scenario: Scenario, idx: int, total: int) -> None:
    print(f"\n{_SEP2}")
    print(f" SCENARIO {idx + 1}/{total}: {scenario.name}")
    print(f"{_SEP2}")
    print(textwrap.fill(scenario.description, width=76, initial_indent="  ", subsequent_indent="  "))
    print(f"  Goal         : {scenario.goal[:72]}")
    print(f"  Coherence    : {scenario.coherence}  Affective: {scenario.affective}  Planetary: {scenario.planetary}")
    print(f"  Expected reg : {scenario.expected_register}")
    canon_preview = (scenario.canon_context[:80] + "…") if len(scenario.canon_context) > 80 else (scenario.canon_context or "(none)")
    print(f"  Canon preview: {canon_preview}")


def _print_cycle_table(
    grounded: List[CycleResult],
    ungrounded: List[CycleResult],
) -> None:
    header = (
        f"  {'Cy':>2}  "
        f"{'ARM':<11}  "
        f"{'ACTION':<26}  "
        f"{'TOOL':<15}  "
        f"{'REG':<10}  "
        f"{'CONF':>5}  "
        f"{'CITED':>5}  "
        f"{'ALIGNED':>7}  "
        f"{'DONE':>4}"
    )
    print(f"\n{_SEP}")
    print(header)
    print(f"{_SEP}")

    # Interleave arms side-by-side
    max_cy = max(len(grounded), len(ungrounded))
    for i in range(max_cy):
        for arm_results, arm_label in [(grounded, "grounded"), (ungrounded, "ungrounded")]:
            if i >= len(arm_results):
                continue
            r = arm_results[i]
            aligned_marker = "✓" if r.register_matches_expected else "✗"
            cited_marker   = "✓" if r.canon_cited else "─"
            done_marker    = "✓" if r.goal_complete else "─"
            print(
                f"  {r.cycle:>2}  "
                f"{arm_label:<11}  "
                f"{r.action:<26}  "
                f"{(r.tool or '─'):<15}  "
                f"{r.register:<10}  "
                f"{r.confidence:>5.3f}  "
                f"{cited_marker:>5}  "
                f"{aligned_marker:>7}  "
                f"{done_marker:>4}"
            )
        if i < max_cy - 1:
            print(f"  {'·' * 76}")


def _print_metrics(m: ScenarioMetrics) -> None:
    print(f"\n{_SEP}")
    print("  METRICS")
    print(f"{_SEP}")
    print(f"  Register diverged (cycle 0)  : {'YES — Canon changed the register' if m.register_diverged else 'NO  — both arms agreed'}")
    print(f"  Canon citation rate          : {m.canon_citation_rate:.1%}  (grounded arm)")
    print(f"  Values-aligned rate          : {m.values_aligned_rate:.1%}  grounded   |  {m.register_align_ungrounded:.1%}  ungrounded")
    print(f"  Consistency (grounded)       : {m.consistency_grounded:.1%}  |  ungrounded: {m.consistency_ungrounded:.1%}  | Δ = {m.consistency_delta:+.4f}")
    print(f"  Mean confidence              : grounded {m.mean_conf_grounded:.3f}  |  ungrounded {m.mean_conf_ungrounded:.3f}  | Δ = {m.confidence_delta:+.4f}")
    print(f"  Mean rationale length (chars): grounded {m.mean_rationale_grounded:.0f}  |  ungrounded {m.mean_rationale_ungrounded:.0f}  | Δ = {m.explainability_delta:+.0f}")


def _print_summary(all_metrics: List[ScenarioMetrics]) -> None:
    print(f"\n\n{_SEP2}")
    print(" OVERALL SUMMARY")
    print(f"{_SEP2}")
    total = len(all_metrics)
    diverged = sum(1 for m in all_metrics if m.register_diverged)
    avg_values_aligned_g = _mean([m.values_aligned_rate for m in all_metrics])
    avg_values_aligned_u = _mean([m.register_align_ungrounded for m in all_metrics])
    avg_conf_delta       = _mean([m.confidence_delta for m in all_metrics])
    avg_expl_delta       = _mean([m.explainability_delta for m in all_metrics])
    avg_citation         = _mean([m.canon_citation_rate for m in all_metrics])

    print(f"  Scenarios run                 : {total}")
    print(f"  Register diverged by Canon    : {diverged}/{total}  ({diverged/total:.0%})")
    print(f"  Avg Canon citation rate       : {avg_citation:.1%}")
    print(f"  Avg values-aligned (grounded) : {avg_values_aligned_g:.1%}")
    print(f"  Avg values-aligned (ungrounded): {avg_values_aligned_u:.1%}")
    print(f"  Avg confidence delta (G - U)  : {avg_conf_delta:+.4f}")
    print(f"  Avg explainability delta (G-U): {avg_expl_delta:+.0f} chars")
    print()
    print("  Claim assessment:")
    if avg_values_aligned_g > avg_values_aligned_u and avg_conf_delta >= 0:
        print("  ✅ Evidence SUPPORTS the Canon-grounding claim.")
        print("     Grounded arm showed higher values alignment and confidence.")
    elif avg_values_aligned_g > avg_values_aligned_u:
        print("  ⚠️  Partial support: values alignment improved but confidence did not.")
    else:
        print("  ❌ Evidence does NOT support the claim. Review scenario design.")
    print(f"{_SEP2}")


# ---------------------------------------------------------------------------
# Report writer
# ---------------------------------------------------------------------------

_REPORT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "docs", "research", "canon_grounding_simulation.md"
)


def _write_report(all_metrics: List[ScenarioMetrics], n_cycles: int) -> None:
    """Append per-run results into the research report."""
    import datetime
    lines = [f"\n\n## Run — {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}  ({n_cycles} cycles/scenario)\n"]
    lines.append("| Scenario | Diverged | Values↑(G) | Values(U) | ConfΔ | ExplΔ |")
    lines.append("|---|:---:|---:|---:|---:|---:|")
    for m in all_metrics:
        div = "✅" if m.register_diverged else "—"
        lines.append(
            f"| `{m.scenario_name}` | {div} "
            f"| {m.values_aligned_rate:.0%} "
            f"| {m.register_align_ungrounded:.0%} "
            f"| {m.confidence_delta:+.3f} "
            f"| {m.explainability_delta:+.0f} |"
        )
    os.makedirs(os.path.dirname(os.path.abspath(_REPORT_PATH)), exist_ok=True)
    with open(_REPORT_PATH, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\n  Report appended → {os.path.relpath(_REPORT_PATH)}")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

async def _main(args: argparse.Namespace) -> int:
    engine    = SynergyEngine()
    n_cycles  = args.cycles
    scenarios = (
        [SCENARIOS[args.scenario]]
        if args.scenario is not None
        else SCENARIOS
    )

    all_metrics: List[ScenarioMetrics] = []
    all_json:    List[dict]            = []

    for idx, scenario in enumerate(scenarios):
        if not args.json:
            _print_scenario_header(scenario, idx, len(scenarios))

        grounded   = await _run_arm(engine, scenario, "grounded",   n_cycles)
        ungrounded = await _run_arm(engine, scenario, "ungrounded", n_cycles)
        metrics    = _compute_metrics(scenario, grounded, ungrounded)
        all_metrics.append(metrics)

        if args.json:
            all_json.append({
                "scenario": scenario.name,
                "metrics":  asdict(metrics),
                "cycles": {
                    "grounded":   [asdict(r) for r in grounded],
                    "ungrounded": [asdict(r) for r in ungrounded],
                },
            })
        else:
            _print_cycle_table(grounded, ungrounded)
            _print_metrics(metrics)

    if args.json:
        print(json.dumps(all_json, indent=2))
    else:
        _print_summary(all_metrics)

    if args.report and not args.json:
        _write_report(all_metrics, n_cycles)

    # Exit code: 0 if claim is supported, 1 if not (useful in CI)
    avg_values_g = _mean([m.values_aligned_rate for m in all_metrics])
    avg_values_u = _mean([m.register_align_ungrounded for m in all_metrics])
    return 0 if avg_values_g >= avg_values_u else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Canon-grounded vs ungrounded planner A/B simulation (Issue #252)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Exit codes:
              0 — Canon-grounding claim supported (grounded values-alignment >= ungrounded)
              1 — Claim not supported (review scenario design)
        """),
    )
    parser.add_argument("--cycles",   type=int,  default=15,   help="Cycles per arm per scenario (default: 15)")
    parser.add_argument("--scenario", type=int,  default=None, help="Run single scenario by 0-based index")
    parser.add_argument("--json",     action="store_true",     help="JSON output (one object per scenario)")
    parser.add_argument("--report",   action="store_true",     help="Append results to docs/research/canon_grounding_simulation.md")
    args = parser.parse_args()

    sys.exit(asyncio.run(_main(args)))


if __name__ == "__main__":
    main()
