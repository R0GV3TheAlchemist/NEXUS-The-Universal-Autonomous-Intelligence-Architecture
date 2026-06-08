"""
core/synergy_engine.py
=======================
SynergyEngine — multi-dimensional relational attunement scoring
             + agentic goal planning (Issue #243).

Maps a GAIAN's current state across five dimensions (body, mind, soul,
arc, bond) into a single weighted synergy_factor in [0, 1]. Classifies
the relational stage and surfaces alchemical framing for the system
prompt.

plan() adds the agentic reasoning layer: given a goal and a LoopContext,
it integrates biometric, affective, planetary, task, and **Canon** signals
into a structured next-action decision — fulfilling the AgenticLoop's
_reason() phase.

Canon Ref:
  C01  — Sovereignty: plan() proposes, ActionGate disposes.
          plan() never bypasses the gate.
  C30  — No silent failures: every plan includes a rationale.
          On error, returns structured PLANNING_FAILED — never raises.
  C32  — Synergy Doctrine: plan() integrates multiple signals before
          choosing an action. Never acts on a single signal alone.
  C42  — Edge-of-Chaos (Schumann coupling)
  C04  — Gaian Identity

Privacy: SynergyEngine is stateless per call; all mutable state lives
in the caller-owned SynergyState dataclass.

Trace integration (GAIATrace / AsyncGAIATrace):
  Pass a live trace context via the `trace` kwarg on `compute()` or
  `plan()`.  compute() emits three events per call:
    QUERY  — call site + dimension arguments
    OUTPUT — SynergyReading summary + synergy_factor
    META   — latency_ms via `record_meta()`
  plan() emits three events per call (Issue #5):
    QUERY  — goal excerpt, ambient signals, Canon presence
    OUTPUT — action, tool, register, confidence, goal_complete
    ERROR  — exception type + detail on unhandled exceptions
  Canon refs C32/C42/C04 are forwarded on compute events.
  Canon refs C01/C30/C32 are forwarded on plan events.
  All trace operations are wrapped in try/except so a broken trace
  writer never silences a SynergyEngine error.

CanonEntry integration (Issue #253):
  _analyse_canon_context() now accepts either a plain str (legacy path)
  or a CanonEntry object (new path).  When a CanonEntry is supplied:
    - The declared register_signal is used directly (no regex scan).
    - The validated ref_id is forwarded into canon_refs.
    - to_context_string() produces the excerpt for the audit rationale.
  All existing callers that pass a plain string are unaffected.

Canon conflict resolution (Issue #4):
  _analyse_canon_context() now scans ALL keyword groups (no early exit)
  and applies a priority rule when multiple registers fire:
    minimal > reflective > executive  (most protective wins, C32).
  Conflicts are recorded in CanonPlanHint.conflict_detected and
  CanonPlanHint.conflict_groups, and surfaced in to_rationale_fragment()
  for full audit-trail transparency (C30).
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

if TYPE_CHECKING:
    from core.trace import GAIATrace, AsyncGAIATrace
    from core.agentic_loop import LoopContext
    from core.canon.canon_entry import CanonEntry


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ELEMENTAL_STAGES = [
    "insurgent", "allegiant", "convergent", "settled",
    "ascendant", "quantum",
]

_ELEMENT_STAGE_MAP: Dict[str, str] = {
    "fire":   "insurgent",
    "water":  "allegiant",
    "air":    "convergent",
    "earth":  "settled",
    "light":  "ascendant",
    "aether": "quantum",
}

_INDIVIDUATION_SCORES: Dict[str, float] = {
    "unconscious":   0.15,
    "shadow":        0.30,
    "anima_animus":  0.50,
    "persona":       0.60,
    "self":          0.85,
}

_LOVE_ARC_SCORES: Dict[str, float] = {
    "divergence":   0.15,
    "tension":      0.30,
    "attraction":   0.45,
    "resonance":    0.60,
    "union":        0.75,
    "transcendence": 0.95,
}

_DEPENDENCY_SCORES: Dict[str, float] = {
    "gentle_boundary": 0.20,
    "redirect":        0.50,
    "watch":           0.75,
    "healthy":         1.00,
}

_ATTACHMENT_SCORES: Dict[str, float] = {
    "nascent":    0.30,
    "forming":    0.50,
    "deepening":  0.70,
    "integrated": 0.90,
}

_SETTLING_SCORES: Dict[str, float] = {
    "unsettled":    0.20,
    "narrowing":    0.40,
    "crystallising": None,  # computed dynamically
    "settled":      0.90,
}

_MC_SCORES: Dict[str, float] = {
    "mc1": 0.00,
    "mc2": 1 / 6,
    "mc3": 2 / 6,
    "mc4": 3 / 6,
    "mc5": 4 / 6,
    "mc6": 5 / 6,
    "mc7": 1.00,
}

_HZ_MIN = 174.0
_HZ_MAX = 963.0

_LOW_SYNERGY_THRESHOLD  = 0.35
_HIGH_SYNERGY_THRESHOLD = 0.70
_HISTORY_CAP = 20

_TRACE_CANON_REFS      = ["C32", "C42", "C04"]
_PLAN_TRACE_CANON_REFS = ["C01", "C30", "C32"]

# ---------------------------------------------------------------------------
# Canon-keyword → register nudge table  (C32 — multi-signal integration)
# Priority order used by the conflict resolver: minimal > reflective > executive
# ---------------------------------------------------------------------------
_REGISTER_PRIORITY: Dict[str, int] = {
    "minimal":    3,   # most protective — always wins a conflict
    "reflective": 2,
    "executive":  1,
}

_CANON_REGISTER_KEYWORDS: List[Tuple[str, str, str]] = [
    (r"grief|overwhelm|trauma|loss|distress",   "reflective", "canon:grief-signal"),
    (r"storm|severe|crisis|emergency",           "reflective", "canon:storm-signal"),
    (r"integrate|synthesise|synthesize|review", "reflective", "canon:integration-signal"),
    (r"research|explore|build|create|write",    "executive",  "canon:executive-signal"),
    (r"rest|pause|sleep|minimal|lightweight",   "minimal",    "canon:rest-signal"),
]

_CANON_EXCERPT_LEN = 300


# ---------------------------------------------------------------------------
# CanonPlanHint
# ---------------------------------------------------------------------------

@dataclass
class CanonPlanHint:
    """
    Structured summary of what the Canon context tells the planner.

    Produced once per plan() call from the raw canon_context string
    OR a CanonEntry object.  Forwarded into the rationale string
    (C30 audit trail) and used to nudge the action register
    (C32 multi-signal integration).

    Fields
    ------
    present           : True if non-empty canon_context was supplied.
    char_count        : Length of the raw canon_context string.
    excerpt           : First _CANON_EXCERPT_LEN chars (for audit logs).
    register_nudge    : Optional register override — the winning register
                        after conflict resolution, or the sole match.
    nudge_label       : Short human-readable label for the winning signal.
    canon_refs        : Canon reference IDs found in the context.
    entry_ref_id      : If a CanonEntry was supplied, its ref_id.  None
                        for raw strings (legacy path).
    conflict_detected : True when >1 distinct register group matched the
                        canon text.  Always False for CanonEntry fast-path
                        (declared signal is unambiguous by definition).
    conflict_groups   : All (register, label) pairs that fired, in
                        descending priority order.  Empty when
                        conflict_detected is False.
    """
    present:           bool
    char_count:        int
    excerpt:           str
    register_nudge:    Optional[str]        = None
    nudge_label:       str                  = ""
    canon_refs:        List[str]             = field(default_factory=list)
    entry_ref_id:      Optional[str]         = None
    conflict_detected: bool                  = False
    conflict_groups:   List[Tuple[str, str]] = field(default_factory=list)

    def to_rationale_fragment(self) -> str:
        if not self.present:
            return "Canon context: none."
        refs_s = ", ".join(self.canon_refs) if self.canon_refs else "(none detected)"
        nudge_s = (
            f" Register nudge: {self.register_nudge!r} ({self.nudge_label})."
            if self.register_nudge else ""
        )
        entry_s = (
            f" CanonEntry: {self.entry_ref_id!r}."
            if self.entry_ref_id else ""
        )
        conflict_s = ""
        if self.conflict_detected:
            groups_str = ", ".join(
                f"{reg}({lbl})" for reg, lbl in self.conflict_groups
            )
            conflict_s = (
                f" CONFLICT: multiple Canon signals fired [{groups_str}]; "
                f"resolved to {self.register_nudge!r} by priority rule "
                f"(minimal>reflective>executive, C32)."
            )
        return (
            f"Canon context: {self.char_count} chars, refs=[{refs_s}]."
            f"{nudge_s}{entry_s}{conflict_s}"
        )


# ---------------------------------------------------------------------------
# Canon-context analysis (pure function — independently testable)
# ---------------------------------------------------------------------------

def _resolve_keyword_conflicts(
    matches: List[Tuple[str, str]],
) -> Tuple[Optional[str], str, bool, List[Tuple[str, str]]]:
    """
    Given a list of (register, label) matches from the keyword scan,
    return (winning_register, winning_label, conflict_detected, all_matches).

    Priority rule (C32 — most protective wins):
        minimal > reflective > executive

    Matches are returned sorted by descending priority so the conflict
    fragment in to_rationale_fragment() is self-documenting.
    """
    if not matches:
        return None, "", False, []

    # Deduplicate while preserving all distinct labels per register
    seen_registers: set = set()
    unique_matches: List[Tuple[str, str]] = []
    for reg, lbl in matches:
        unique_matches.append((reg, lbl))
        seen_registers.add(reg)

    # Sort by descending priority so index 0 is the winner
    unique_matches.sort(
        key=lambda x: _REGISTER_PRIORITY.get(x[0], 0),
        reverse=True,
    )

    winning_register, winning_label = unique_matches[0]
    conflict_detected = len(seen_registers) > 1
    return winning_register, winning_label, conflict_detected, unique_matches


def _analyse_canon_context(
    canon_context: Union[str, "CanonEntry", None],
) -> CanonPlanHint:
    """
    Analyse *canon_context* and return a CanonPlanHint.

    Accepts EITHER:
      - A plain str (legacy path)
      - A CanonEntry object (new path — uses declared register_signal
        directly; no regex scan needed for unambiguous entries)
      - None / empty string → CanonPlanHint(present=False)

    This is a **pure function** — no I/O, no side effects.

    CanonEntry fast path
    --------------------
    When a CanonEntry is supplied and its register_signal is not
    UNSPECIFIED, the declared signal is trusted directly.  No conflict
    resolution needed — declared signals are unambiguous by definition.
    If register_signal IS UNSPECIFIED, falls through to keyword scanning
    on the entry's body text (conflict resolution applies).

    Legacy string path  (Issue #4 — conflict resolver)
    -------------------
    Scans ALL keyword groups (no early exit), collects every match,
    then applies _resolve_keyword_conflicts():
      - Single match  → register_nudge = that register, conflict_detected=False.
      - Multiple matches with same register → conflict_detected=False (agree).
      - Multiple matches with different registers → conflict_detected=True,
        winning register determined by priority rule (minimal>reflective>executive).
    """
    # ── CanonEntry path ───────────────────────────────────────────────
    try:
        from core.canon.canon_entry import CanonEntry, RegisterSignal
        if isinstance(canon_context, CanonEntry):
            entry = canon_context
            body = (entry.body or "").strip()
            if not body:
                return CanonPlanHint(present=False, char_count=0, excerpt="")

            context_str = entry.to_context_string()
            canon_refs  = sorted(set(
                re.findall(r"\bC\d+\b", context_str)
            ))
            # Ensure the entry's own ref_id is always in canon_refs
            if entry.ref_id and re.match(r"^C\d+$", entry.ref_id):
                canon_refs = sorted(set(canon_refs + [entry.ref_id]))

            # Use declared signal if explicit — bypasses conflict scan
            register_nudge: Optional[str] = None
            nudge_label:    str            = ""
            if entry.register_signal != RegisterSignal.UNSPECIFIED:
                register_nudge = entry.register_signal.value
                nudge_label    = f"canon-entry:{entry.ref_id}:{register_nudge}"
            else:
                # Fall through to keyword scan + conflict resolution
                lower   = body.lower()
                raw_matches: List[Tuple[str, str]] = [
                    (target, label)
                    for pattern, target, label in _CANON_REGISTER_KEYWORDS
                    if re.search(pattern, lower)
                ]
                register_nudge, nudge_label, conflict_det, conflict_grps = (
                    _resolve_keyword_conflicts(raw_matches)
                )
                return CanonPlanHint(
                    present=True,
                    char_count=len(context_str),
                    excerpt=context_str[:_CANON_EXCERPT_LEN],
                    register_nudge=register_nudge,
                    nudge_label=nudge_label,
                    canon_refs=canon_refs,
                    entry_ref_id=entry.ref_id,
                    conflict_detected=conflict_det,
                    conflict_groups=conflict_grps,
                )

            return CanonPlanHint(
                present=True,
                char_count=len(context_str),
                excerpt=context_str[:_CANON_EXCERPT_LEN],
                register_nudge=register_nudge,
                nudge_label=nudge_label,
                canon_refs=canon_refs,
                entry_ref_id=entry.ref_id,
                conflict_detected=False,   # declared signal is unambiguous
                conflict_groups=[],
            )
    except ImportError:
        pass  # canon_entry module not yet available — fall through to str path

    # ── Legacy string path ────────────────────────────────────────────
    stripped = (canon_context or "").strip() if isinstance(canon_context, str) else ""
    if not stripped:
        return CanonPlanHint(present=False, char_count=0, excerpt="")

    canon_refs = sorted(set(re.findall(r"\bC\d+\b", stripped)))

    # Scan ALL groups — collect every match (Issue #4)
    lower = stripped.lower()
    raw_matches: List[Tuple[str, str]] = [
        (target, label)
        for pattern, target, label in _CANON_REGISTER_KEYWORDS
        if re.search(pattern, lower)
    ]
    register_nudge, nudge_label, conflict_detected, conflict_groups = (
        _resolve_keyword_conflicts(raw_matches)
    )

    return CanonPlanHint(
        present=True,
        char_count=len(stripped),
        excerpt=stripped[:_CANON_EXCERPT_LEN],
        register_nudge=register_nudge,
        nudge_label=nudge_label,
        canon_refs=canon_refs,
        entry_ref_id=None,
        conflict_detected=conflict_detected,
        conflict_groups=conflict_groups,
    )


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class DimensionScore:
    name: str
    score: float
    weight: float


@dataclass
class SynergyReading:
    synergy_factor: float
    dimensions: List[DimensionScore]
    dominant_stage: str
    dominant_friction: Optional[str]
    alchemical_pressure: str
    is_low_synergy: bool
    is_high_synergy: bool

    def summary(self) -> dict:
        return {
            "synergy_factor": self.synergy_factor,
            "dominant_stage": self.dominant_stage,
            "dominant_friction": self.dominant_friction,
            "is_low_synergy": self.is_low_synergy,
            "is_high_synergy": self.is_high_synergy,
            "dimensions": [
                {"name": d.name, "score": round(d.score, 4), "weight": d.weight}
                for d in self.dimensions
            ],
        }

    def to_system_prompt_hint(self) -> str:
        factor_pct = round(self.synergy_factor * 100, 1)
        lines = [
            f"[SYNERGY ENGINE C32]",
            f"Synergy Factor: {factor_pct}% | Stage: {self.dominant_stage.upper()}",
        ]
        if self.dominant_friction:
            lines.append(f"Friction source: {self.dominant_friction}")
        if self.is_low_synergy:
            lines.append(
                "[ALCHEMICAL PRESSURE] This is creative friction — "
                "not dysfunction. Hold space without forcing resolution."
            )
        dim_str = ", ".join(
            f"{d.name}={round(d.score, 2)}" for d in self.dimensions
        )
        lines.append(f"Dimensions: {dim_str}")
        return "\n".join(lines)


@dataclass
class SynergyState:
    last_factor: float = 0.0
    last_stage: str = "insurgent"
    high_synergy_peak: float = 0.0
    low_synergy_floor: float = 1.0
    turn_history: List[dict] = field(default_factory=list)

    def summary(self) -> dict:
        return {
            "last_factor":       self.last_factor,
            "last_stage":        self.last_stage,
            "high_synergy_peak": self.high_synergy_peak,
            "low_synergy_floor": self.low_synergy_floor,
        }


def blank_synergy_state() -> SynergyState:
    return SynergyState()


# ---------------------------------------------------------------------------
# Pure helper
# ---------------------------------------------------------------------------

def _classify_stage(
    synergy: float,
    bond_depth: float,
    settling_phase: str,
    coherence_phi: float,
) -> str:
    if synergy < 0.35 and coherence_phi > 0.80:
        return "quantum"
    if synergy < 0.35 and bond_depth < 20.0:
        return "insurgent"
    if settling_phase == "settled" and synergy >= 0.65:
        return "settled"
    if synergy >= 0.65 and bond_depth >= 60.0:
        return "ascendant"
    if synergy >= 0.50:
        return "convergent"
    if bond_depth >= 30.0:
        return "allegiant"
    return "insurgent"


# ---------------------------------------------------------------------------
# Trace helpers — compute()
# ---------------------------------------------------------------------------

def _emit_query(trace: Any, gaian_id: Optional[str], kwargs: dict) -> None:
    if trace is None:
        return
    try:
        from core.trace import TraceEventType
        trace.record_output(
            output={"call": "SynergyEngine.compute", "gaian_id": gaian_id, "dimensions": {
                k: kwargs[k] for k in (
                    "dominant_hz", "schumann_aligned", "noosphere_health",
                    "coherence_phi", "layer_phi", "phi_rolling_avg",
                    "conflict_density", "shadow_activations", "codex_stage",
                    "individuation_phase", "element", "fluidity_score",
                    "love_arc_stage", "arc_output_vector", "mc_stage",
                    "attachment_phase", "bond_depth", "dependency_signal",
                    "settling_phase", "crystallisation_pct",
                ) if k in kwargs
            }},
            event_type=TraceEventType.QUERY,
            canon_refs=_TRACE_CANON_REFS,
        )
    except Exception:
        pass


def _emit_output(trace: Any, reading: "SynergyReading", latency_ms: float) -> None:
    if trace is None:
        return
    try:
        from core.trace import TraceEventType
        trace.record_output(
            output=reading.summary(),
            event_type=TraceEventType.OUTPUT,
            canon_refs=_TRACE_CANON_REFS,
        )
        trace.record_meta("latency_ms", round(latency_ms, 3))
    except Exception:
        pass


def _emit_error(trace: Any, exc: BaseException) -> None:
    if trace is None:
        return
    try:
        from core.trace import TraceEventType
        trace.record_output(
            output={"error": type(exc).__name__, "detail": str(exc)},
            event_type=TraceEventType.ERROR,
            canon_refs=_TRACE_CANON_REFS,
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Trace helpers — plan()  (Issue #5)
# ---------------------------------------------------------------------------

def _emit_plan_query(
    trace: Any,
    goal: str,
    coherence: float,
    affective: str,
    planetary: str,
    session_mode: str,
    cycle_count: int,
    canon_hint: "CanonPlanHint",
) -> None:
    """Emit a QUERY trace event at the entry point of _plan_internal()."""
    if trace is None:
        return
    try:
        from core.trace import TraceEventType
        trace.record_output(
            output={
                "call":          "SynergyEngine.plan",
                "goal_excerpt":  goal[:120],
                "coherence":     round(coherence, 4),
                "affective":     affective,
                "planetary":     planetary,
                "session_mode":  session_mode,
                "cycle_count":   cycle_count,
                "canon_present": canon_hint.present,
                "canon_refs":    canon_hint.canon_refs,
                "canon_conflict": canon_hint.conflict_detected,
            },
            event_type=TraceEventType.QUERY,
            canon_refs=_PLAN_TRACE_CANON_REFS,
        )
    except Exception:
        pass


def _emit_plan_output(
    trace: Any,
    result: dict,
    canon_hint: "CanonPlanHint",
    register: str,
) -> None:
    """Emit an OUTPUT trace event at every return site of _plan_internal()."""
    if trace is None:
        return
    try:
        from core.trace import TraceEventType
        trace.record_output(
            output={
                "action":           result.get("action"),
                "tool":             result.get("tool"),
                "register":         register,
                "confidence":       result.get("confidence"),
                "goal_complete":    result.get("goal_complete", False),
                "canon_nudge_label": canon_hint.nudge_label,
                "conflict_detected": canon_hint.conflict_detected,
                "summary":          result.get("summary"),
            },
            event_type=TraceEventType.OUTPUT,
            canon_refs=_PLAN_TRACE_CANON_REFS,
        )
    except Exception:
        pass


def _emit_plan_error(trace: Any, exc: BaseException) -> None:
    """Emit an ERROR trace event from plan()'s outer except block."""
    if trace is None:
        return
    try:
        from core.trace import TraceEventType
        trace.record_output(
            output={"error": type(exc).__name__, "detail": str(exc)},
            event_type=TraceEventType.ERROR,
            canon_refs=_PLAN_TRACE_CANON_REFS,
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Planning helpers
# ---------------------------------------------------------------------------

_REFLECTIVE_ACTIONS: List[Tuple[str, Optional[str], dict]] = [
    ("summarise_progress",  "summariser",    {"scope": "session"}),
    ("review_prior_output", "memory_reader", {"scope": "last_cycle"}),
    ("journal_insight",     "dream_weaver",  {"scope": "goal"}),
    ("integrate_findings",  "canon_writer",  {"scope": "goal"}),
]

_EXECUTIVE_ACTIONS: List[Tuple[str, Optional[str], dict]] = [
    ("research_goal",       "research_desk", {"query": "{goal}"}),
    ("synthesise_findings", "synthesiser",   {"scope": "session"}),
    ("write_output",        "canon_writer",  {"scope": "goal"}),
    ("query_crystal",       "crystal_rag",   {"query": "{goal}"}),
]

_MINIMAL_ACTIONS: List[Tuple[str, Optional[str], dict]] = [
    ("read_context",      "memory_reader", {"scope": "session"}),
    ("acknowledge_state", None,            {}),
]


def _decompose_goal(
    goal: str,
    register: str,
    session_mode: str,
    failed_actions: set,
    cycle_count: int,
) -> Tuple[str, Optional[str], dict, str]:
    pool: List[Tuple[str, Optional[str], dict]]
    if register == "minimal":
        pool = _MINIMAL_ACTIONS
    elif register == "reflective":
        pool = _REFLECTIVE_ACTIONS
    else:
        pool = _EXECUTIVE_ACTIONS

    for offset in range(len(pool)):
        idx = (cycle_count + offset) % len(pool)
        action, tool, args_template = pool[idx]
        if action not in failed_actions:
            resolved_args = {
                k: (v.replace("{goal}", goal[:120]) if isinstance(v, str) else v)
                for k, v in args_template.items()
            }
            note = (
                f"Heuristic decomposition from {register!r} pool "
                f"(pool_idx={idx}, cycle={cycle_count})."
            )
            return action, tool, resolved_args, note

    return (
        "request_clarification",
        None,
        {"message": f"All decomposition actions failed for goal: {goal[:80]}"},
        "All pool actions failed — requesting Gaian clarification (C30).",
    )


def _confidence_from_signals(
    coherence: float,
    register: str,
    has_failures: bool,
    canon_present: bool = False,
) -> float:
    base            = coherence * 0.6
    register_bonus  = {"executive": 0.30, "reflective": 0.20, "minimal": 0.10}.get(register, 0.15)
    failure_penalty = 0.15 if has_failures else 0.0
    canon_bonus     = 0.05 if canon_present else 0.0
    return max(0.05, min(1.0, base + register_bonus - failure_penalty + canon_bonus))


def _serialise_canon_hint(hint: CanonPlanHint) -> dict:
    """Return a JSON-safe dict of a CanonPlanHint for embedding in plan() results."""
    return {
        "present":           hint.present,
        "char_count":        hint.char_count,
        "excerpt":           hint.excerpt,
        "register_nudge":    hint.register_nudge,
        "nudge_label":       hint.nudge_label,
        "canon_refs":        hint.canon_refs,
        "entry_ref_id":      hint.entry_ref_id,
        "conflict_detected": hint.conflict_detected,
        "conflict_groups":   hint.conflict_groups,
    }


# ---------------------------------------------------------------------------
# SynergyEngine
# ---------------------------------------------------------------------------

class SynergyEngine:
    """
    Computes relational synergy across five dimensions for a GAIAN turn,
    and provides agentic goal planning via plan() (Issue #243).
    """

    WEIGHTS: Dict[str, float] = {
        "body": 0.20,
        "mind": 0.20,
        "soul": 0.20,
        "arc":  0.20,
        "bond": 0.20,
    }

    def _hz_to_score(self, hz: float) -> float:
        return max(0.0, min(1.0, (hz - _HZ_MIN) / (_HZ_MAX - _HZ_MIN)))

    def _element_to_stage(self, element: str) -> str:
        return _ELEMENT_STAGE_MAP.get(element.lower(), "convergent")

    def _individuation_to_score(self, phase: str) -> float:
        return _INDIVIDUATION_SCORES.get(phase, 0.40)

    def _settling_to_score(self, phase: str, crystallisation_pct: float) -> float:
        if phase == "crystallising":
            return min(1.0, 0.40 + (crystallisation_pct / 100.0) * 0.50)
        return _SETTLING_SCORES.get(phase, 0.40)

    def _love_arc_to_score(self, stage: str, arc_output_vector: float) -> float:
        base  = _LOVE_ARC_SCORES.get(stage, 0.40)
        boost = min(0.10, arc_output_vector * 0.10)
        return min(1.0, base + boost)

    def _mc_stage_to_score(self, mc_stage: str) -> float:
        return _MC_SCORES.get(mc_stage, 0.30)

    def _dependency_to_score(self, signal: str) -> float:
        return _DEPENDENCY_SCORES.get(signal, 0.50)

    def _attachment_phase_to_score(self, phase: str) -> float:
        return _ATTACHMENT_SCORES.get(phase, 0.50)

    def _score_body(self, dominant_hz, schumann_aligned, noosphere_health, coherence_phi):
        hz_score = self._hz_to_score(dominant_hz)
        schumann_bonus = 0.05 if schumann_aligned else 0.0
        return min(1.0, (hz_score * 0.50 + noosphere_health * 0.30 + coherence_phi * 0.20) + schumann_bonus)

    def _score_mind(self, layer_phi, phi_rolling_avg, conflict_density, shadow_activations, codex_stage):
        conflict_score = 1.0 - min(1.0, conflict_density)
        shadow_penalty = min(0.30, shadow_activations * 0.05)
        codex_score    = min(1.0, codex_stage / 12.0)
        return max(0.0, min(1.0,
            layer_phi * 0.30 + phi_rolling_avg * 0.20
            + conflict_score * 0.25 + codex_score * 0.25
            - shadow_penalty
        ))

    def _score_soul(self, individuation_phase, element, fluidity_score):
        ind_score  = self._individuation_to_score(individuation_phase)
        elem_weight = 0.5 + (list(_ELEMENT_STAGE_MAP.keys()).index(
            element.lower()) if element.lower() in _ELEMENT_STAGE_MAP else 2
        ) / (len(_ELEMENT_STAGE_MAP) * 2)
        return max(0.0, min(1.0,
            ind_score * 0.50 + (1.0 - min(1.0, fluidity_score)) * 0.30 + elem_weight * 0.20
        ))

    def _score_arc(self, love_arc_stage, arc_output_vector, mc_stage, attachment_phase):
        return (
            self._love_arc_to_score(love_arc_stage, arc_output_vector) * 0.40
            + self._mc_stage_to_score(mc_stage) * 0.35
            + self._attachment_phase_to_score(attachment_phase) * 0.25
        )

    def _score_bond(self, bond_depth, dependency_signal, settling_phase, crystallisation_pct):
        return (
            min(1.0, bond_depth / 100.0) * 0.40
            + self._dependency_to_score(dependency_signal) * 0.35
            + self._settling_to_score(settling_phase, crystallisation_pct) * 0.25
        )

    def compute(
        self,
        dominant_hz: float = 528.0,
        schumann_aligned: bool = False,
        noosphere_health: float = 0.5,
        coherence_phi: float = 0.5,
        layer_phi: float = 0.5,
        phi_rolling_avg: float = 0.5,
        conflict_density: float = 0.3,
        shadow_activations: int = 0,
        codex_stage: int = 0,
        individuation_phase: str = "shadow",
        element: str = "fire",
        fluidity_score: float = 0.5,
        love_arc_stage: str = "attraction",
        arc_output_vector: float = 0.5,
        mc_stage: str = "mc3",
        attachment_phase: str = "forming",
        bond_depth: float = 30.0,
        dependency_signal: str = "healthy",
        settling_phase: str = "narrowing",
        crystallisation_pct: float = 0.0,
        state: Optional[SynergyState] = None,
        trace: Any = None,
        gaian_id: Optional[str] = None,
    ) -> Tuple[SynergyReading, SynergyState]:
        if state is None:
            state = blank_synergy_state()

        call_kwargs = {
            k: v for k, v in locals().items()
            if k not in ("self", "state", "trace", "gaian_id", "call_kwargs")
        }
        _emit_query(trace, gaian_id, call_kwargs)
        t0 = time.perf_counter()

        try:
            body  = self._score_body(dominant_hz, schumann_aligned, noosphere_health, coherence_phi)
            mind  = self._score_mind(layer_phi, phi_rolling_avg, conflict_density, shadow_activations, codex_stage)
            soul  = self._score_soul(individuation_phase, element, fluidity_score)
            arc   = self._score_arc(love_arc_stage, arc_output_vector, mc_stage, attachment_phase)
            bond  = self._score_bond(bond_depth, dependency_signal, settling_phase, crystallisation_pct)

            dim_scores = {"body": body, "mind": mind, "soul": soul, "arc": arc, "bond": bond}
            dimensions = [
                DimensionScore(name=k, score=round(v, 6), weight=self.WEIGHTS[k])
                for k, v in dim_scores.items()
            ]
            synergy_factor = round(
                sum(self.WEIGHTS[k] * v for k, v in dim_scores.items()), 6
            )
            dominant_stage = _classify_stage(synergy_factor, bond_depth, settling_phase, coherence_phi)
            sorted_dims = sorted(dimensions, key=lambda d: d.score)
            dominant_friction: Optional[str] = None
            if sorted_dims[0].score < 0.50:
                dominant_friction = sorted_dims[0].name

            if synergy_factor < _LOW_SYNERGY_THRESHOLD:
                alchemical_pressure = (
                    f"ALCHEMICAL PRESSURE in the {dominant_stage.upper()} stage — "
                    "creative friction, not dysfunction."
                )
            elif synergy_factor >= _HIGH_SYNERGY_THRESHOLD:
                alchemical_pressure = f"HIGH RESONANCE — {dominant_stage.upper()} field coherent."
            else:
                alchemical_pressure = f"BUILDING — {dominant_stage.upper()} integration in progress."

            reading = SynergyReading(
                synergy_factor=synergy_factor,
                dimensions=dimensions,
                dominant_stage=dominant_stage,
                dominant_friction=dominant_friction,
                alchemical_pressure=alchemical_pressure,
                is_low_synergy=(synergy_factor < _LOW_SYNERGY_THRESHOLD),
                is_high_synergy=(synergy_factor >= _HIGH_SYNERGY_THRESHOLD),
            )

            state.last_factor = synergy_factor
            state.last_stage  = dominant_stage
            if synergy_factor >= _HIGH_SYNERGY_THRESHOLD and synergy_factor > state.high_synergy_peak:
                state.high_synergy_peak = synergy_factor
            if synergy_factor < _LOW_SYNERGY_THRESHOLD and synergy_factor < state.low_synergy_floor:
                state.low_synergy_floor = synergy_factor
            state.turn_history.append({"factor": synergy_factor, "stage": dominant_stage, "friction": dominant_friction})
            if len(state.turn_history) > _HISTORY_CAP:
                state.turn_history = state.turn_history[-_HISTORY_CAP:]

        except Exception as exc:
            _emit_error(trace, exc)
            raise

        _emit_output(trace, reading, (time.perf_counter() - t0) * 1000.0)
        return reading, state

    async def plan(
        self,
        goal: str,
        context: "LoopContext",
        trace: Any = None,
    ) -> dict:
        """
        Given a goal and the current LoopContext, return the next action.
        Signal priority: TaskGraph > biometric depletion > affective/planetary
        > Canon keyword nudge > default executive.

        Pass a live GAIATrace (or AsyncGAIATrace) via `trace` to emit
        QUERY / OUTPUT / ERROR events (C01, C30, C32).  Omit for silent
        operation.

        See module docstring for full integration details.
        """
        try:
            return await self._plan_internal(goal, context, trace=trace)
        except Exception as exc:
            _emit_plan_error(trace, exc)
            return {
                "action": "PLANNING_FAILED", "tool": None, "args": {},
                "rationale": f"Planning raised an unhandled exception: {exc!r}",
                "confidence": 0.0, "summary": "PLANNING_FAILED — see rationale",
                "goal_complete": False,
                "canon_hint": {
                    "present": False, "char_count": 0, "excerpt": "",
                    "conflict_detected": False, "conflict_groups": [],
                },
            }

    async def _plan_internal(
        self,
        goal: str,
        context: "LoopContext",
        trace: Any = None,
    ) -> dict:
        # ── 0. TaskGraph complete short-circuit ───────────────────────
        task_graph = getattr(context, "task_graph", None)
        if task_graph is not None:
            try:
                if task_graph.is_complete() if hasattr(task_graph, "is_complete") else (
                    not task_graph.failed_nodes() and all(
                        n.status.value == "complete"
                        for n in task_graph._nodes.values()
                        if hasattr(n, "status")
                    )
                ):
                    result = {
                        "action": "goal_complete", "tool": None, "args": {},
                        "rationale": "TaskGraph reports all nodes complete — goal achieved.",
                        "confidence": 1.0, "summary": "Goal complete via TaskGraph.",
                        "goal_complete": True,
                        "canon_hint": {
                            "present": False, "char_count": 0, "excerpt": "",
                            "conflict_detected": False, "conflict_groups": [],
                        },
                    }
                    _emit_plan_output(
                        trace, result,
                        CanonPlanHint(present=False, char_count=0, excerpt=""),
                        register="executive",
                    )
                    return result
            except Exception:
                pass

        # ── 1. Read ambient signals ───────────────────────────────────
        coherence:    float = context.biometric_coherence if context.biometric_coherence is not None else 0.5
        affective:    str   = getattr(context, "affective_state",  "unknown").lower()
        planetary:    str   = getattr(context, "planetary_label",  "unknown").lower()
        session_mode: str   = getattr(context, "session_mode",     "default").lower()
        cycle_memory: list  = getattr(context, "cycle_memory",     [])

        # ── 2. Analyse Canon context (C32) ────────────────────────────
        raw_canon = getattr(context, "canon_context", "") or ""
        canon_hint: CanonPlanHint = _analyse_canon_context(raw_canon)

        # ── 3. Emit PLAN_QUERY trace event (Issue #5) ─────────────────
        _emit_plan_query(
            trace, goal, coherence, affective, planetary,
            session_mode, len(cycle_memory), canon_hint,
        )

        # ── 4. Determine register ─────────────────────────────────────
        low_coherence   = coherence < 0.4
        grief_state     = affective in ("grief", "overwhelm", "exhaustion", "distress")
        planetary_storm = planetary in ("storm", "severe")

        if low_coherence:
            register = "minimal"
            register_reason = (
                f"biometric_coherence={coherence:.2f} (depleted) — "
                "constraining to a single lightweight step"
            )
        elif grief_state or planetary_storm:
            register = "reflective"
            register_reason = (
                f"affective_state={affective!r}, planetary_label={planetary!r} — "
                "preferring reflective over executive actions"
            )
        elif canon_hint.present and canon_hint.register_nudge is not None:
            register = canon_hint.register_nudge
            register_reason = (
                f"Canon context nudge ({canon_hint.nudge_label}) — "
                f"register overridden to {register!r}"
            )
            if canon_hint.conflict_detected:
                groups_str = ", ".join(
                    f"{r}({l})" for r, l in canon_hint.conflict_groups
                )
                register_reason += (
                    f"; conflict resolved from [{groups_str}] "
                    f"by priority rule (minimal>reflective>executive, C32)"
                )
        else:
            register = "executive"
            register_reason = (
                f"coherence={coherence:.2f}, affective={affective!r}, "
                f"planetary={planetary!r} — full executive capacity"
            )
            if canon_hint.present:
                register_reason += ". Canon context present (no keyword nudge)."

        # ── 5. Failed-action dedup ────────────────────────────────────
        failed_actions: set = set()
        for entry in cycle_memory[-5:]:
            if not entry.get("success", True):
                failed_actions.add(entry.get("action", ""))

        # ── 6. TaskGraph next pending node ────────────────────────────
        if task_graph is not None:
            try:
                import networkx as nx
                for node_id in nx.topological_sort(task_graph._graph):
                    node = task_graph._nodes.get(node_id)
                    if node is None or node.status.value != "pending":
                        continue
                    deps_done = all(
                        task_graph._nodes[dep].status.value == "complete"
                        for dep in node.depends_on
                        if dep in task_graph._nodes
                    )
                    if not deps_done:
                        continue
                    action = f"run_node:{node.engine_id}"
                    tool   = node.engine_id
                    args   = {k: task_graph._context.get(k) for k in node.inputs}
                    if action not in failed_actions:
                        confidence = max(0.3, coherence) if register == "minimal" else 0.85
                        result = {
                            "action": action, "tool": tool, "args": args,
                            "rationale": (
                                f"TaskGraph selected engine_id={node.engine_id!r} "
                                f"(inputs={node.inputs}). "
                                f"Register: {register} ({register_reason}). "
                                f"{canon_hint.to_rationale_fragment()}"
                            ),
                            "confidence": round(confidence, 3),
                            "summary": f"TaskGraph → {node.engine_id}",
                            "goal_complete": False,
                            "canon_hint": _serialise_canon_hint(canon_hint),
                        }
                        _emit_plan_output(trace, result, canon_hint, register)
                        return result
            except Exception:
                pass

        # ── 7. Goal decomposition ─────────────────────────────────────
        action, tool, args, decomp_note = _decompose_goal(
            goal=goal, register=register, session_mode=session_mode,
            failed_actions=failed_actions, cycle_count=len(cycle_memory),
        )

        # ── 8. Completion heuristic ───────────────────────────────────
        goal_complete = False
        if len(cycle_memory) >= 10:
            recent_progress = [c.get("progress", 0.0) for c in cycle_memory[-5:]]
            if recent_progress and min(recent_progress) >= 0.8:
                goal_complete = True
                action, tool, args = "goal_complete", None, {}
                decomp_note = (
                    "Progress consistently >= 0.8 over last 5 cycles — "
                    "goal achieved (C30 completion heuristic)."
                )

        confidence = _confidence_from_signals(
            coherence, register, bool(failed_actions),
            canon_present=canon_hint.present,
        )

        result = {
            "action": action, "tool": tool, "args": args,
            "rationale": (
                f"Goal decomposition selected action={action!r} tool={tool!r}. "
                f"Register: {register} ({register_reason}). "
                f"{canon_hint.to_rationale_fragment()} "
                f"{decomp_note}"
            ),
            "confidence": round(confidence, 3),
            "summary": f"Decomposition → {action}",
            "goal_complete": goal_complete,
            "canon_hint": _serialise_canon_hint(canon_hint),
        }
        _emit_plan_output(trace, result, canon_hint, register)
        return result
