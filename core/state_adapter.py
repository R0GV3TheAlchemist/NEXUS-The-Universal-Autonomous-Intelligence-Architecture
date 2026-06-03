"""
core/state_adapter.py
GAIA Philosophy/Runtime Boundary — Sprint G-7

The single, explicit layer that translates GAIA's rich metaphysical domain
objects (Solfeggio frequencies, Jungian phases, love arc stages, Schumann
alignment, coherence scores, affective valence, bond depth) into the typed
numeric inputs that SynergyEngine.compute() expects.

NO other module may perform this translation. Every call site must use:

    adapter = GAIAStateAdapter(gaian_record)
    params  = adapter.to_synergy_params()
    reading, new_state = engine.compute(**params)

Or, using the convenience bridge on SynergyEngine (added in this sprint):

    reading, new_state = engine.compute_from_adapter(adapter)

Canon Refs:
  C32  Synergy Doctrine — philosophy and runtime are both honored,
       at the right abstraction level.
  C01  Sovereignty — the translation is explicit, auditable, single-source.

Migration Plan:
  G-7  (this PR)  Build adapter; wire all call sites via **params.
  G-8             Add SynergyEngine.compute_from_params(SynergyParams)
                  as the canonical entry point; deprecate bare signature.
  G-9             Remove bare-parameter signature entirely.
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, TypedDict

log = logging.getLogger(__name__)

# ── Optional GAIATrace integration (graceful if trace not yet available) ──── #
try:
    from core.trace import AsyncGAIATrace, GAIATrace, TraceEventType
    _TRACE_AVAILABLE = True
except ImportError:  # pragma: no cover — trace module not yet on path
    _TRACE_AVAILABLE = False


# ── Solfeggio frequency table ─────────────────────────────────────────────── #
# Canonical mapping: solfeggio note name → Hz value.
# Extend here (and only here) when new notes are added to the domain.
SOLFEGGIO_HZ: Dict[str, float] = {
    "ut":   396.0,   # Liberating Guilt and Fear
    "re":   417.0,   # Undoing Situations and Facilitating Change
    "mi":   528.0,   # Transformation and Miracles (DNA Repair / Heart Coherence)
    "fa":   639.0,   # Connecting / Relationships
    "sol":  741.0,   # Awakening Intuition
    "la":   852.0,   # Returning to Spiritual Order
    "si":   963.0,   # Awakening / Return to Oneness
}

SCHUMANN_BASELINE_HZ: float = 7.83  # Earth's fundamental electromagnetic resonance
SCHUMANN_HARMONIC_TOLERANCE: float = 0.10  # ±10% harmonic window

# Floating-point micro-residual floor: modulo results below this value are
# treated as exactly zero.  Chosen to be well below any physically meaningful
# difference while safely absorbing IEEE-754 rounding noise.
# e.g.  15.66 % 7.83 → 7.82999999999999929 (residual from exact multiple)
# After normalisation: (7.83 - 7.829999...) / 7.83 ≈ 9e-14  → clamped to 0
_SCHUMANN_FLOAT_EPSILON: float = 1e-9


# ── Typed contract between adapter and SynergyEngine ────────────────────── #

class SynergyParams(TypedDict):
    """All numeric/string primitives that SynergyEngine.compute() expects.

    Rules:
    - All values must be JSON-serialisable primitives (float, int, str, bool).
    - No domain objects (GaianRecord, enum instances, etc.) may appear here.
    - GAIAStateAdapter is the ONLY producer of this dict.
    - SynergyEngine is the ONLY consumer.
    """
    dominant_hz:         float   # Solfeggio Hz in [174, 963]
    individuation_phase: str     # Jungian phase label e.g. 'shadow', 'self'
    love_arc_stage:      str     # Relationship arc stage e.g. 'awakening'
    schumann_aligned:    bool    # Personal Hz harmonically aligns with Schumann
    coherence_score:     float   # [0.0, 1.0] biometric/psychological coherence
    emotional_valence:   float   # [-1.0, 1.0] affective valence
    bond_depth:          float   # [0.0, 1.0] relational bond depth


# ── Adapter ───────────────────────────────────────────────────────────────── #

class GAIAStateAdapter:
    """Translates a GaianRecord (or any duck-typed state object) into the
    SynergyParams TypedDict that SynergyEngine.compute() expects.

    This is the ONLY place in the codebase where domain metaphysics meet
    runtime numerics. All other call sites use this adapter.

    Attributes:
        record: The source GaianRecord or compatible state object.
        canon_refs: Canon entries this adapter honours (C32, C01).

    Usage::

        adapter = GAIAStateAdapter(gaian_record)
        params  = adapter.to_synergy_params()          # SynergyParams dict
        result  = engine.compute(**params)

        # Or inspect individual resolved values:
        hz      = adapter.resolved_hz()                # float
        aligned = adapter.resolved_schumann_aligned()  # bool
    """

    CANON_REFS: List[str] = ["C32", "C01"]

    def __init__(self, record: Any) -> None:
        """
        Args:
            record: Any object that exposes the Gaian state fields via
                    attribute access.  Missing attributes always fall back
                    to safe defaults — no AttributeError is ever raised.
        """
        self._record = record

    # ── Public API ────────────────────────────────────────────────────────── #

    def to_synergy_params(self) -> SynergyParams:
        """Resolve all fields and return a fully-typed SynergyParams dict.

        Emits a GAIATrace TOOL_CALL event if core.trace is available.
        Never raises — any resolver failure falls back to the field default.
        """
        gaian_id = self._safe_get("id", None)

        if _TRACE_AVAILABLE:
            with GAIATrace(
                event=TraceEventType.TOOL_CALL,
                gaian_id=gaian_id,
                canon_refs=self.CANON_REFS,
                inputs={"gaian_id": gaian_id, "record_type": type(self._record).__name__},
            ) as trace:
                params = self._build_params()
                trace.record_output({"params_keys": list(params.keys()), "dominant_hz": params["dominant_hz"]})
                return params
        else:
            return self._build_params()

    # ── Convenience resolvers (public, for inspection / testing) ─────────── #

    def resolved_hz(self) -> float:
        """Return the resolved Solfeggio Hz for the record."""
        return self._resolve_hz()

    def resolved_individuation_phase(self) -> str:
        return self._resolve_individuation()

    def resolved_love_arc_stage(self) -> str:
        return self._resolve_love_arc()

    def resolved_schumann_aligned(self) -> bool:
        return self._resolve_schumann_alignment()

    def resolved_coherence(self) -> float:
        return self._resolve_coherence()

    def resolved_emotional_valence(self) -> float:
        return self._resolve_emotional_valence()

    def resolved_bond_depth(self) -> float:
        return self._resolve_bond_depth()

    # ── Private builder ───────────────────────────────────────────────────── #

    def _build_params(self) -> SynergyParams:
        return SynergyParams(
            dominant_hz=self._resolve_hz(),
            individuation_phase=self._resolve_individuation(),
            love_arc_stage=self._resolve_love_arc(),
            schumann_aligned=self._resolve_schumann_alignment(),
            coherence_score=self._resolve_coherence(),
            emotional_valence=self._resolve_emotional_valence(),
            bond_depth=self._resolve_bond_depth(),
        )

    # ── Private resolvers ─────────────────────────────────────────────────── #
    # Each resolver encapsulates EXACTLY ONE translation rule.
    # None of them know about each other; none of them touch SynergyEngine.
    # All clamp/validate at the boundary so SynergyEngine receives clean data.

    def _resolve_hz(self) -> float:
        """Map Gaian's active Solfeggio note to Hz.

        Priority:
        1. ``dominant_hz`` float attribute (already numeric — pass through).
        2. ``active_solfeggio_note`` string looked up in SOLFEGGIO_HZ table.
        3. Default: 528.0 Hz (heart coherence / transformation).
        """
        raw_hz = self._safe_get("dominant_hz", None)
        if isinstance(raw_hz, (int, float)) and raw_hz > 0:
            return float(raw_hz)

        note = self._safe_get("active_solfeggio_note", "mi")
        hz = SOLFEGGIO_HZ.get(str(note).lower(), 528.0)
        return hz

    def _resolve_individuation(self) -> str:
        """Return the Jungian individuation phase label.

        Valid labels (non-exhaustive): 'persona', 'shadow', 'anima',
        'animus', 'self'.  Unknown values are passed through as-is;
        SynergyEngine is responsible for range validation.
        """
        return str(self._safe_get("jungian_phase", "persona"))

    def _resolve_love_arc(self) -> str:
        """Return the love arc stage label.

        Valid labels: 'dormant', 'awakening', 'deepening', 'sovereign',
        'transcendent'.  Unknown values passed through.
        """
        return str(self._safe_get("love_arc_stage", "awakening"))

    def _resolve_schumann_alignment(self) -> bool:
        """Determine whether the Gaian's dominant Hz is in Schumann harmonic.

        Algorithm
        ---------
        Compute the fractional position of ``hz`` within one Schumann period::

            harmonic_phase = (hz % schumann) / schumann

        The value is aligned when it lies within SCHUMANN_HARMONIC_TOLERANCE
        (10%) of either the *lower* boundary (0.0) or the *upper* boundary
        (1.0), i.e. near a harmonic node.

        Float-precision fixes (see _SCHUMANN_FLOAT_EPSILON)
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        IEEE-754 modulo of exact integer multiples produces micro-residuals:

            15.66 % 7.83  →  7.82999999999999929   (should be 0.0)

        Without correction, ``(7.83 - 7.830e0) / 7.83 ≈ 9e-14`` lands
        *inside* the upper window only by luck; for other multiples it can
        miss entirely.  The fix: if the raw modulo exceeds
        ``schumann - _SCHUMANN_FLOAT_EPSILON`` we treat it as exactly
        ``schumann`` (i.e. phase 0.0 of the next cycle).

        Non-finite / degenerate schumann guard
        ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        Sensors may supply NaN, ±inf, zero, or a negative value for
        ``schumann_hz``.  All non-finite and non-positive values return
        ``False`` (not aligned) rather than propagating NaN arithmetic
        into SynergyEngine.

        Explicit override
        ~~~~~~~~~~~~~~~~~
        Falls back to the boolean ``schumann_aligned`` attribute when present
        (allows external sensors to override the computed value).
        """
        explicit = self._safe_get("schumann_aligned", None)
        if isinstance(explicit, bool):
            return explicit

        hz = self._resolve_hz()
        schumann_raw = self._safe_get("schumann_hz", SCHUMANN_BASELINE_HZ)

        try:
            schumann = float(schumann_raw)
        except (TypeError, ValueError):
            return False

        # Guard: non-finite or non-positive baseline → not aligned
        if not math.isfinite(schumann) or schumann <= 0.0:
            return False

        # Compute fractional harmonic phase with IEEE-754 residual correction.
        # math.fmod mirrors C fmod — same precision as %, but explicit.
        raw_mod = math.fmod(hz, schumann)

        # Correct upward-biased residuals: if the modulo is within epsilon of
        # a full period, snap it to 0.0 (start of next cycle).
        if raw_mod >= schumann - _SCHUMANN_FLOAT_EPSILON:
            raw_mod = 0.0

        # Correct downward-biased residuals: tiny negatives from fmod on
        # negative hz inputs (defensive; hz should always be positive).
        if raw_mod < 0.0:
            raw_mod = 0.0

        harmonic_phase = raw_mod / schumann

        return (
            harmonic_phase < SCHUMANN_HARMONIC_TOLERANCE
            or harmonic_phase > (1.0 - SCHUMANN_HARMONIC_TOLERANCE)
        )

    def _resolve_coherence(self) -> float:
        """Return HRV coherence score clamped to [0.0, 1.0]."""
        raw = self._safe_get("hrv_coherence_score",
              self._safe_get("coherence_score", 0.5))
        try:
            return max(0.0, min(1.0, float(raw)))
        except (TypeError, ValueError):
            return 0.5

    def _resolve_emotional_valence(self) -> float:
        """Return affective valence clamped to [-1.0, 1.0]."""
        raw = self._safe_get("affective_valence",
              self._safe_get("emotional_valence", 0.0))
        try:
            return max(-1.0, min(1.0, float(raw)))
        except (TypeError, ValueError):
            return 0.0

    def _resolve_bond_depth(self) -> float:
        """Return relational bond depth clamped to [0.0, 1.0]."""
        raw = self._safe_get("bond_depth", 0.5)
        try:
            return max(0.0, min(1.0, float(raw)))
        except (TypeError, ValueError):
            return 0.5

    # ── Utility ───────────────────────────────────────────────────────────── #

    def _safe_get(self, attr: str, default: Any) -> Any:
        """getattr with a silent fallback — never raises AttributeError."""
        return getattr(self._record, attr, default)

    def __repr__(self) -> str:
        gaian_id = self._safe_get("id", "<unknown>")
        return f"GAIAStateAdapter(gaian_id={gaian_id!r})"


# ── Async variant ─────────────────────────────────────────────────────────── #

class AsyncGAIAStateAdapter(GAIAStateAdapter):
    """Async-aware drop-in for GAIAStateAdapter.

    to_synergy_params() is still sync (resolver logic is pure CPU work),
    but the async context manager wraps the trace emission in AsyncGAIATrace
    when available, keeping the trace coroutine-safe.
    """

    async def to_synergy_params_async(self) -> SynergyParams:  # type: ignore[override]
        gaian_id = self._safe_get("id", None)

        if _TRACE_AVAILABLE:
            async with AsyncGAIATrace(
                event=TraceEventType.TOOL_CALL,
                gaian_id=gaian_id,
                canon_refs=self.CANON_REFS,
                inputs={"gaian_id": gaian_id, "record_type": type(self._record).__name__},
            ) as trace:
                params = self._build_params()
                trace.record_output({"params_keys": list(params.keys()), "dominant_hz": params["dominant_hz"]})
                return params
        else:
            return self._build_params()


# ── Module-level self-test (python -m core.state_adapter) ─────────────────── #

if __name__ == "__main__":  # pragma: no cover
    import json

    class _MockRecord:
        id = "gaian-test-001"
        active_solfeggio_note = "fa"   # 639 Hz — Connecting/Relationships
        jungian_phase = "shadow"
        love_arc_stage = "deepening"
        hrv_coherence_score = 0.77
        affective_valence = 0.42
        bond_depth = 0.88
        # schumann_hz omitted → uses baseline 7.83

    adapter = GAIAStateAdapter(_MockRecord())
    params = adapter.to_synergy_params()
    print(json.dumps(params, indent=2))
    print(f"\nSchumann aligned: {adapter.resolved_schumann_aligned()}")
    print(f"Repr: {adapter!r}")
