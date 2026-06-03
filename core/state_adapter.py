"""
core/state_adapter.py
GAIA Philosophy/Runtime Boundary — Sprint G-7

The single, explicit layer that translates GAIA's rich metaphysical domain
objects (Solfeggio frequencies, Jungian phases, love arc stages, Schumann
resonance) into the flat, serialisable SynergyParams dict consumed by the
Synergy Engine and all downstream systems.

Design goals
------------
* Zero leakage: the Synergy Engine never imports GAIA domain types directly.
* Testable: every resolver is a pure function or a thin method on a dataclass.
* Traceable: optional Trace injection records every resolution step.

Public surface
--------------
GAIAStateAdapter          — synchronous adapter (used in most contexts)
AsyncGAIAStateAdapter     — async wrapper (for async callers)
SynergyParams             — TypedDict contract for the output dict
SOLFEGGIO_HZ              — canonical note-name → Hz mapping
SCHUMANN_BASELINE_HZ      — Earth baseline resonance frequency
SCHUMANN_HARMONIC_TOLERANCE — ±% window for alignment detection
_TRACE_AVAILABLE          — bool flag: True when core.trace is importable

Canon refs: C30, C31, C34, C37
"""
from __future__ import annotations

import math
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    pass

# ── Trace availability flag ────────────────────────────────────────────────── #
# Allows tests and callers to branch on whether the trace subsystem is present.
try:
    from core.trace import Trace  # noqa: F401
    _TRACE_AVAILABLE: bool = True
except ImportError:
    _TRACE_AVAILABLE: bool = False


# ── Solfeggio frequency table ──────────────────────────────────────────────── #
# Canonical mapping: solfeggio note name → Hz value.
# Used by _resolve_hz() to convert a string note name into a numeric frequency.
SOLFEGGIO_HZ: Dict[str, float] = {
    "ut":  396.0,   # Liberating Guilt and Fear
    "re":  417.0,   # Undoing Situations and Facilitating Change
    "mi":  528.0,   # Transformation and Miracles (DNA Repair / Heart Coherence)
    "fa":  639.0,   # Connecting/Relationships
    "sol": 741.0,   # Awakening Intuition
    "la":  852.0,   # Returning to Spiritual Order
    "si":  963.0,   # Divine Consciousness / Enlightenment
    # Extended set (sometimes included)
    "174": 174.0,
    "285": 285.0,
}

# ── Schumann resonance constants ───────────────────────────────────────────── #
SCHUMANN_BASELINE_HZ: float = 7.88  # Earth's fundamental electromagnetic resonance (corrected)
SCHUMANN_HARMONIC_TOLERANCE: float = 0.10  # ±10% harmonic window

# Internal float-comparison epsilon.
# IEEE-754 double precision produces residuals like:
#   e.g.  15.66 % 7.83 → 7.82999999999999929 (residual from exact multiple)
# After normalisation: (7.83 - 7.829999...) / 7.83 ≈ 9e-14  → clamped to 0
# We use a generous 1e-9 so we catch all such cases without touching real data.
_SCHUMANN_FLOAT_EPSILON: float = 1e-9


# ── SynergyParams TypedDict ────────────────────────────────────────────────── #

class SynergyParams(dict):
    """Typed contract for the flat param dict consumed by the Synergy Engine.

    Inherits from dict so it serialises naturally to JSON / msgpack.
    Type annotations are documentation only — no runtime enforcement.

    Keys
    ----
    dominant_hz          : float   Solfeggio Hz in [174, 963]
    individuation_phase  : str     Jung individuation phase label
    love_arc_stage       : str     Current love arc stage label
    schumann_aligned     : bool    Whether dominant_hz aligns with Schumann harmonics
    coherence_score      : float   [0, 1] composite coherence
    emotional_valence    : float   [-1, 1] valence (negative → distress, positive → flourishing)
    bond_depth           : float   [0, 1] relational bond depth
    """


# ── Trace protocol ─────────────────────────────────────────────────────────── #

class _NullTrace:
    """No-op trace used when no trace is injected."""
    def record_input(self, data: dict) -> None:  # noqa: ARG002
        pass
    def record_output(self, data: dict) -> None:  # noqa: ARG002
        pass


# ── GAIAStateAdapter ───────────────────────────────────────────────────────── #

class GAIAStateAdapter:
    """Translate a Gaian record into a flat SynergyParams dict.

    Parameters
    ----------
    record : Any
        A Gaian state record with optional attributes:
        ``dominant_hz``, ``active_solfeggio_note``, ``individuation_phase``,
        ``love_arc_stage``, ``schumann_aligned``, ``schumann_hz``,
        ``coherence_score``, ``emotional_valence``, ``bond_depth``.
    trace : optional
        An object with ``record_input(dict)`` and ``record_output(dict)``
        methods. Defaults to a no-op trace.

    Usage
    -----
    ::

        adapter = GAIAStateAdapter(record)
        params  = adapter.to_synergy_params()
        # params["dominant_hz"] → 528.0
        # params["schumann_aligned"] → True
    """

    def __init__(self, record: Any, trace: Any = None) -> None:
        self._record = record
        self._trace  = trace or _NullTrace()

    def __repr__(self) -> str:
        """Return a readable representation including record ID if available."""
        record_id = getattr(self._record, 'id', None) or 'unknown'
        return f"<GAIAStateAdapter(id={record_id})>"

    # ── Public resolvers ────────────────────────────────────────────────────── #

    def to_synergy_params(self) -> SynergyParams:
        """Resolve all fields and return a flat SynergyParams dict."""
        self._trace.record_input({
            "record_type": type(self._record).__name__,
        })

        hz      = self._resolve_hz()                # float
        phase   = self._resolve_individuation()     # str
        arc     = self._resolve_love_arc()          # str
        aligned = self._resolve_schumann()          # bool
        coh     = self._resolve_coherence()         # float
        valence = self._resolve_valence()           # float
        bond    = self._resolve_bond()              # float

        params = SynergyParams(
            dominant_hz         = hz,
            individuation_phase = phase,
            love_arc_stage      = arc,
            schumann_aligned    = aligned,
            coherence_score     = coh,
            emotional_valence   = valence,
            bond_depth          = bond,
        )

        self._trace.record_output({"params_keys": list(params.keys()), "dominant_hz": params["dominant_hz"]})
        return params

    def resolved_hz(self) -> float:
        """Return the resolved Solfeggio frequency in Hz."""
        return self._resolve_hz()

    def resolved_individuation_phase(self) -> str:
        """Return the resolved Jungian individuation phase label."""
        return self._resolve_individuation()

    def resolved_love_arc_stage(self) -> str:
        """Return the resolved love arc stage label."""
        return self._resolve_love_arc()

    def resolved_schumann_aligned(self) -> bool:
        """Return True if the dominant Hz is harmonically aligned with Schumann."""
        return self._resolve_schumann()

    @property
    def resolved_coherence(self) -> float:
        """Return the resolved coherence score [0, 1]."""
        return self._resolve_coherence()

    @property
    def resolved_emotional_valence(self) -> float:
        """Return the resolved emotional valence [-1, 1]."""
        return self._resolve_valence()

    @property
    def resolved_bond_depth(self) -> float:
        """Return the resolved bond depth [0, 1]."""
        return self._resolve_bond()

    # ── Private resolvers ───────────────────────────────────────────────────── #

    def _resolve_hz(self) -> float:
        """Resolve dominant Hz from the record.

        Resolution order:
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
        return str(self._safe_get("individuation_phase", "persona"))

    def _resolve_love_arc(self) -> str:
        return str(self._safe_get("love_arc_stage", "awakening"))

    def _resolve_coherence(self) -> float:
        v = self._safe_get("coherence_score", 0.5)
        return float(max(0.0, min(1.0, v)))

    def _resolve_valence(self) -> float:
        v = self._safe_get("emotional_valence", 0.0)
        return float(max(-1.0, min(1.0, v)))

    def _resolve_bond(self) -> float:
        v = self._safe_get("bond_depth", 0.5)
        return float(max(0.0, min(1.0, v)))

    def _resolve_schumann(self) -> bool:
        """Resolve Schumann harmonic alignment for the dominant Hz.

        Algorithm
        ---------
        Compute the fractional position of ``hz`` within one Schumann period::

            harmonic_phase = (hz % schumann) / schumann

        A value near 0 or 1 indicates the Hz is close to an exact harmonic
        multiple of the Schumann frequency.  We consider it *aligned* when::

            harmonic_phase < SCHUMANN_HARMONIC_TOLERANCE
            OR
            harmonic_phase > (1 - SCHUMANN_HARMONIC_TOLERANCE)

        Float-precision fixes (see _SCHUMANN_FLOAT_EPSILON)
        -----------------------------------------------------
        IEEE-754 fmod can yield a residual very close to ``schumann`` instead
        of 0 when ``hz`` is an exact multiple.  For example::

            15.66 % 7.83  →  7.82999999999999929   (should be 0.0)

        We snap ``raw_mod`` to 0 when it is within ``_SCHUMANN_FLOAT_EPSILON``
        of either 0 or ``schumann``, and to ``schumann`` equivalently.

        Explicit override
        -----------------
        If the record carries a ``schumann_aligned`` bool attribute, that
        value is returned directly without computation.

        Parameters
        ----------
        The method reads ``schumann_hz`` from the record (defaults to
        ``schumann_hz``).  All non-finite and non-positive values return
        ``False`` defensively.
        """
        # Explicit override — caller knows best
        explicit = self._safe_get("schumann_aligned", None)
        if isinstance(explicit, bool):
            return explicit

        hz = self._resolve_hz()
        schumann_raw = self._safe_get("schumann_hz", SCHUMANN_BASELINE_HZ)

        # Defensive: reject degenerate inputs
        try:
            schumann = float(schumann_raw)
        except (TypeError, ValueError):
            schumann = SCHUMANN_BASELINE_HZ

        if not math.isfinite(hz) or hz <= 0:
            return False
        if not math.isfinite(schumann) or schumann <= 0:
            return False

        raw_mod = math.fmod(hz, schumann)

        # Snap floating-point residuals at exact harmonic multiples.
        # negative hz inputs (defensive; hz should always be positive).
        if raw_mod < 0:
            raw_mod += schumann

        # If raw_mod is within epsilon of schumann, it's a residual of an
        # exact multiple — treat as 0.
        if raw_mod >= schumann - _SCHUMANN_FLOAT_EPSILON:
            raw_mod = 0.0
        elif raw_mod <= _SCHUMANN_FLOAT_EPSILON:
            raw_mod = 0.0

        harmonic_phase = raw_mod / schumann

        return (
            harmonic_phase < SCHUMANN_HARMONIC_TOLERANCE
            or harmonic_phase > (1.0 - SCHUMANN_HARMONIC_TOLERANCE)
        )

    def _safe_get(self, attr: str, default: Any) -> Any:
        """Safely retrieve an attribute from the record, returning default on miss."""
        try:
            val = getattr(self._record, attr, default)
            return val if val is not None else default
        except Exception:
            return default


# ── AsyncGAIAStateAdapter ──────────────────────────────────────────────────── #

class AsyncGAIAStateAdapter(GAIAStateAdapter):
    """Async-compatible wrapper around GAIAStateAdapter.

    Exposes the same resolvers as coroutines so async callers don't need
    to wrap them manually.  All resolution logic lives in the synchronous
    parent class.

    Usage
    -----
    ::

        adapter = AsyncGAIAStateAdapter(record)
        params  = await adapter.to_synergy_params_async()
    """

    async def to_synergy_params_async(self) -> SynergyParams:
        """Async version of :meth:`GAIAStateAdapter.to_synergy_params`."""
        self._trace.record_input({"record_type": type(self._record).__name__})

        hz      = self._resolve_hz()
        phase   = self._resolve_individuation()
        arc     = self._resolve_love_arc()
        aligned = self._resolve_schumann()
        coh     = self._resolve_coherence()
        valence = self._resolve_valence()
        bond    = self._resolve_bond()

        params = SynergyParams(
            dominant_hz         = hz,
            individuation_phase = phase,
            love_arc_stage      = arc,
            schumann_aligned    = aligned,
            coherence_score     = coh,
            emotional_valence   = valence,
            bond_depth          = bond,
        )

        self._trace.record_output({"params_keys": list(params.keys()), "dominant_hz": params["dominant_hz"]})
        return params

    async def resolved_hz_async(self) -> float:
        return self._resolve_hz()

    async def resolved_schumann_aligned_async(self) -> bool:
        return self._resolve_schumann()
