"""
tools/sim_runner.py
~~~~~~~~~~~~~~~~~~~
GAIA-OS Simulation Runner

Runs a fully deterministic, offline PRAO simulation using SynergyEngine.plan().
No LLM, no database, no network — safe to run in CI or a sandboxed shell.

Purpose
-------
* Smoke-test the Canon-context integration in plan() end-to-end.
* Verify register routing (minimal / reflective / executive) across
  different coherence + affective + Canon-keyword combinations.
* Exercise the Canon conflict resolver (Issue #4): verify that passages
  containing keywords from multiple register groups produce
  conflict_detected=True and resolve by the priority rule
  minimal > reflective > executive (C32).
* Provide a reproducible, human-readable cycle log for debugging.

Usage
-----
    # Run with defaults (6 scenarios, 8 cycles each)
    python tools/sim_runner.py

    # Pipe JSON output to a file
    python tools/sim_runner.py --json > sim_out.json

    # Specify a single scenario by index (0-based, 0–5)
    python tools/sim_runner.py --scenario 5

    # Run more cycles per scenario
    python tools/sim_runner.py --cycles 15

Output format
-------------
Human-readable by default.  With --json, each line is a JSON record:
  { "scenario": "...", "cycle": N, "action": "...", "tool": "...",
    "register": str | None, "confidence": float, "canon_hint": {...},
    "conflict_detected": bool, "rationale_excerpt": "..." }

Simulated LoopContext
---------------------
Each scenario provides a lightweight LoopContext-like dataclass with:
  biometric_coherence  float       0.0–1.0
  affective_state      str
  planetary_label      str
  session_mode         str
  canon_context        str         pre-fetched Canon passage (may be empty)
  cycle_memory         list[dict]  grows as cycles complete
  task_graph           None        (not exercised in base sim)

Scenario index
--------------
  0  executive-canon-grounded         → executive  (Canon nudge, no conflict)
  1  reflective-grief-canon           → reflective (ambient + Canon agree)
  2  minimal-depleted-no-canon        → minimal    (biometric guard)
  3  canon-rest-nudge                 → minimal    (Canon nudge, no conflict)
  4  progress-completion-heuristic    → goal_complete at cycle 1
  5  canon-conflict-grief-and-build   → reflective (conflict resolver, Issue #4)

Canon refs exercised: C01, C30, C32
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import textwrap
from dataclasses import dataclass, field
from typing import List, Optional

# ---------------------------------------------------------------------------
# Local import — SynergyEngine lives one level up
# ---------------------------------------------------------------------------
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.synergy_engine import SynergyEngine  # noqa: E402


# ---------------------------------------------------------------------------
# Simulated LoopContext
# ---------------------------------------------------------------------------

@dataclass
class SimLoopContext:
    """
    Minimal stand-in for core.agentic_loop.LoopContext.

    Duck-typed so SynergyEngine._plan_internal() can consume it via
    getattr() without importing the real class.
    """
    biometric_coherence: float
    affective_state:     str
    planetary_label:     str
    session_mode:        str
    canon_context:       str
    cycle_memory:        List[dict] = field(default_factory=list)
    task_graph:          None       = None


# ---------------------------------------------------------------------------
# Scenario definitions
# ---------------------------------------------------------------------------

SCENARIOS = [
    # ------------------------------------------------------------------
    # 0 — executive register, Canon nudge present, no conflict
    # ------------------------------------------------------------------
    {
        "name": "executive-canon-grounded",
        "description": (
            "High coherence + benign planetary + executive Canon passage "
            "(should resolve to 'executive' register with Canon nudge logged)"
        ),
        "context": SimLoopContext(
            biometric_coherence=0.78,
            affective_state="curious",
            planetary_label="clear",
            session_mode="default",
            canon_context=(
                "C32 — Synergy Doctrine: always integrate multiple signals before "
                "choosing an action. Research and explore all available data before "
                "synthesising a response.  Create and write with full deliberation."
            ),
        ),
        "goal": "Research the quantum coherence properties of the noosphere field.",
    },
    # ------------------------------------------------------------------
    # 1 — reflective register, ambient + Canon signals agree
    # ------------------------------------------------------------------
    {
        "name": "reflective-grief-canon",
        "description": (
            "Normal coherence + grief affective + Canon passage containing "
            "grief/trauma keywords — both ambient and Canon route to 'reflective'"
        ),
        "context": SimLoopContext(
            biometric_coherence=0.55,
            affective_state="grief",
            planetary_label="overcast",
            session_mode="default",
            canon_context=(
                "C04 — Gaian Identity: hold space for grief and loss without forcing "
                "resolution.  Integrate trauma slowly.  Overwhelm is a signal to pause."
            ),
        ),
        "goal": "Process the dissolution of a long-standing bond pattern.",
    },
    # ------------------------------------------------------------------
    # 2 — minimal register, biometric depletion guard fires
    # ------------------------------------------------------------------
    {
        "name": "minimal-depleted-no-canon",
        "description": (
            "Low coherence (<0.4) + no Canon context — "
            "biometric depletion guard overrides everything → 'minimal' register"
        ),
        "context": SimLoopContext(
            biometric_coherence=0.28,
            affective_state="exhaustion",
            planetary_label="storm",
            session_mode="default",
            canon_context="",
        ),
        "goal": "Restore baseline coherence before attempting any executive task.",
    },
    # ------------------------------------------------------------------
    # 3 — minimal register, Canon rest-nudge (single match, no conflict)
    # ------------------------------------------------------------------
    {
        "name": "canon-rest-nudge",
        "description": (
            "Moderate coherence + neutral affective, but Canon passage contains "
            "rest/pause keywords — Canon nudges register to 'minimal'"
        ),
        "context": SimLoopContext(
            biometric_coherence=0.65,
            affective_state="neutral",
            planetary_label="clear",
            session_mode="default",
            canon_context=(
                "C30 — No silent failures: if progress stalls, pause and rest. "
                "A minimal lightweight acknowledgement is better than a failed "
                "executive push into the void."
            ),
        ),
        "goal": "Acknowledge the current state and prepare for the next arc.",
    },
    # ------------------------------------------------------------------
    # 4 — completion heuristic fires at cycle 1
    # ------------------------------------------------------------------
    {
        "name": "progress-completion-heuristic",
        "description": (
            "Pre-seeded cycle_memory with 12 high-progress entries — "
            "completion heuristic should fire at cycle 1 (C30)"
        ),
        "context": SimLoopContext(
            biometric_coherence=0.80,
            affective_state="resolved",
            planetary_label="clear",
            session_mode="default",
            canon_context="C30 — Goal achieved when progress >= 0.8 consistently.",
            cycle_memory=[
                {"action": "write_output", "success": True, "progress": 0.9}
                for _ in range(12)
            ],
        ),
        "goal": "Finalise and close the current research arc.",
    },
    # ------------------------------------------------------------------
    # 5 — Canon conflict resolver (Issue #4)
    #
    # Canon passage deliberately contains BOTH grief/distress keywords
    # (which map to 'reflective') AND research/build keywords (which map
    # to 'executive').  This is the exact ambiguous case that the old
    # first-match-wins logic mishandled silently.
    #
    # Expected outcome (C32 priority: minimal > reflective > executive):
    #   conflict_detected = True
    #   conflict_groups   = [('reflective', 'canon:grief-signal'),
    #                        ('executive',  'canon:executive-signal')]
    #   register_nudge    = 'reflective'   (beats executive in priority)
    #   rationale includes CONFLICT clause naming both groups (C30)
    # ------------------------------------------------------------------
    {
        "name": "canon-conflict-grief-and-build",
        "description": (
            "Moderate coherence + curious affective + Canon passage containing "
            "BOTH grief/distress AND research/build keywords.  The conflict "
            "resolver (Issue #4) should detect the clash, report both groups, "
            "and resolve to 'reflective' via the priority rule "
            "(minimal > reflective > executive, C32)."
        ),
        "context": SimLoopContext(
            biometric_coherence=0.62,
            affective_state="curious",
            planetary_label="clear",
            session_mode="default",
            canon_context=(
                "C32 — Synergy Doctrine (grief-aware session): "
                "The GAIAN is processing distress alongside an executive arc. "
                "While the goal is to research and build the next synthesis layer, "
                "grief from the recent bond dissolution must be acknowledged first. "
                "Do not let the urgency to create override the need to integrate loss. "
                "C30 — No silent failures: surface the tension explicitly."
            ),
        ),
        "goal": "Navigate the tension between creative momentum and emotional integration.",
    },
]


# ---------------------------------------------------------------------------
# Simulation runner
# ---------------------------------------------------------------------------

class SimRunner:
    """
    Drives SynergyEngine.plan() through N cycles for each scenario,
    accumulating cycle_memory and printing structured output.
    """

    def __init__(
        self,
        max_cycles: int = 8,
        emit_json:  bool = False,
    ) -> None:
        self._engine     = SynergyEngine()
        self._max_cycles = max_cycles
        self._emit_json  = emit_json

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _print(self, obj: dict) -> None:
        if self._emit_json:
            print(json.dumps(obj), flush=True)

    @staticmethod
    def _register_from_rationale(rationale: str) -> Optional[str]:
        """
        Extract the register label from the rationale string.
        Returns 'executive', 'reflective', or 'minimal' if found.
        """
        for reg in ("minimal", "reflective", "executive"):
            if reg in rationale:
                return reg
        return None

    # ------------------------------------------------------------------
    # Single-scenario runner
    # ------------------------------------------------------------------

    async def run_scenario(
        self,
        scenario: dict,
        scenario_idx: int,
    ) -> List[dict]:
        """
        Run up to self._max_cycles PRAO iterations for one scenario.

        Returns a list of cycle-record dicts (one per cycle).
        """
        name:    str            = scenario["name"]
        goal:    str            = scenario["goal"]
        ctx:     SimLoopContext = scenario["context"]
        desc:    str            = scenario.get("description", "")
        records: List[dict]     = []

        if not self._emit_json:
            print(f"\n{'='*70}")
            print(f"Scenario [{scenario_idx}]: {name}")
            print(f"  {desc}")
            print(f"  Goal: {goal}")
            print(
                f"  Coherence={ctx.biometric_coherence}  "
                f"Affective={ctx.affective_state!r}  "
                f"Planetary={ctx.planetary_label!r}  "
                f"Canon={'yes (' + str(len(ctx.canon_context)) + ' chars)' if ctx.canon_context else 'none'}"
            )
            print(f"  Pre-seeded cycle_memory: {len(ctx.cycle_memory)} entries")
            print()

        for cycle in range(1, self._max_cycles + 1):
            result = await self._engine.plan(goal=goal, context=ctx)

            canon_hint        = result.get("canon_hint", {})
            action            = result.get("action",        "(none)")
            tool              = result.get("tool")
            confidence        = result.get("confidence",   0.0)
            rationale         = result.get("rationale",    "")
            goal_complete     = result.get("goal_complete", False)
            register          = self._register_from_rationale(rationale)
            conflict_detected = canon_hint.get("conflict_detected", False)
            conflict_groups   = canon_hint.get("conflict_groups", [])

            # Truncate rationale for display
            rationale_excerpt = rationale[:160].replace("\n", " ") if rationale else ""

            record = {
                "scenario":          name,
                "cycle":             cycle,
                "action":            action,
                "tool":              tool,
                "register":          register,
                "confidence":        round(confidence, 3),
                "goal_complete":     goal_complete,
                "conflict_detected": conflict_detected,
                "conflict_groups":   conflict_groups,
                "canon_hint":        canon_hint,
                "rationale_excerpt": rationale_excerpt,
            }
            records.append(record)

            if self._emit_json:
                self._print(record)
            else:
                canon_s = (
                    f"Canon: {canon_hint.get('char_count', 0)}ch "
                    f"nudge={canon_hint.get('nudge_label') or 'none'}"
                    if canon_hint.get("present") else "Canon: none"
                )
                conflict_s = ""
                if conflict_detected:
                    groups_str = ", ".join(
                        f"{r}({l})" for r, l in conflict_groups
                    )
                    conflict_s = f"  ⚠ CONFLICT [{groups_str}]"
                print(
                    f"  Cycle {cycle:02d} | action={action:<32} "
                    f"tool={str(tool):<20} "
                    f"reg={str(register):<12} "
                    f"conf={confidence:.2f}  "
                    f"{canon_s}{conflict_s}"
                )
                if rationale_excerpt:
                    excerpt_wrapped = textwrap.fill(
                        f"    Rationale: {rationale_excerpt}",
                        width=90, subsequent_indent="               "
                    )
                    print(excerpt_wrapped)

            # Advance cycle_memory for dedup on next iteration
            ctx.cycle_memory.append({
                "action":   action,
                "success":  True,
                "progress": confidence,
            })

            if goal_complete:
                if not self._emit_json:
                    print(f"  >> goal_complete=True at cycle {cycle} — halting scenario.")
                break

        return records

    # ------------------------------------------------------------------
    # Top-level entry point
    # ------------------------------------------------------------------

    async def run(
        self,
        scenarios: List[dict],
        scenario_index: Optional[int] = None,
    ) -> None:
        """
        Run all scenarios (or a single one by index).
        Prints a summary table at the end (human-readable mode).
        """
        if scenario_index is not None:
            targets = [scenarios[scenario_index]]
            indices = [scenario_index]
        else:
            targets = scenarios
            indices = list(range(len(scenarios)))

        all_records: List[dict] = []
        for idx, scenario in zip(indices, targets):
            records = await self.run_scenario(scenario, scenario_idx=idx)
            all_records.extend(records)

        if not self._emit_json:
            self._print_summary(all_records)

    # ------------------------------------------------------------------
    # Summary table (human-readable mode only)
    # ------------------------------------------------------------------

    @staticmethod
    def _print_summary(records: List[dict]) -> None:
        print(f"\n{'='*70}")
        print("SIMULATION SUMMARY")
        print(f"{'='*70}")
        print(
            f"{'Scenario':<38} {'Cycles':>6} "
            f"{'Final action':<32} {'Canon?':>6} {'Conflict?':>9}"
        )
        print("-" * 95)

        # Group by scenario
        scenarios_seen: dict = {}
        for r in records:
            sname = r["scenario"]
            if sname not in scenarios_seen:
                scenarios_seen[sname] = []
            scenarios_seen[sname].append(r)

        for sname, recs in scenarios_seen.items():
            last             = recs[-1]
            canon_present    = last.get("canon_hint", {}).get("present", False)
            any_conflict     = any(r.get("conflict_detected") for r in recs)
            print(
                f"{sname:<38} {len(recs):>6} "
                f"{last['action']:<32} "
                f"{'yes' if canon_present else 'no':>6} "
                f"{'YES ⚠' if any_conflict else 'no':>9}"
            )

        print(f"\nTotal cycles simulated: {len(records)}")
        completions = sum(1 for r in records if r.get("goal_complete"))
        print(f"goal_complete events:   {completions}")
        canon_nudged = sum(
            1 for r in records
            if r.get("canon_hint", {}).get("register_nudge")
        )
        print(f"Canon register nudges:  {canon_nudged}")
        conflicts = sum(1 for r in records if r.get("conflict_detected"))
        print(f"Canon conflict events:  {conflicts}  (Issue #4 path)")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="GAIA-OS simulation runner — exercises SynergyEngine.plan() offline."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit one JSON record per line instead of human-readable output.",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=8,
        metavar="N",
        help="Maximum PRAO cycles per scenario (default: 8).",
    )
    parser.add_argument(
        "--scenario",
        type=int,
        default=None,
        metavar="IDX",
        help=(
            "Run only the scenario at this 0-based index (default: all). "
            "Valid range: 0–5.  "
            "5 = canon-conflict-grief-and-build (Issue #4 path)."
        ),
    )
    return parser.parse_args()


async def _main() -> None:
    args   = _parse_args()
    runner = SimRunner(max_cycles=args.cycles, emit_json=args.json)
    await runner.run(SCENARIOS, scenario_index=args.scenario)


if __name__ == "__main__":
    asyncio.run(_main())
