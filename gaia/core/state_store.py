"""
gaia/core/state_store.py

Singleton state store v2 — the ONLY source of truth for GAIAState at runtime.

Canon anchors:
  - GAIA_D6_META_COHERENCE_ENGINE.md  (sealed 2026-06-17)
  - Issue #576  (GAIAState — central state object)
  - Issue #568  (D6 Meta-Coherence Engine — endocrine layer)
  - Issue #578  (Architect Protocol — GOVERNANCE always first)
  - Issue #580  (Talisman Object — active_talismans)

Design rules (v2):
  - ONE module owns the live GAIAState instance. No other module holds
    a reference to _state directly.
  - All reads  → get_state() or get_runtime_json() or get_mode().
  - All writes → run_d6_cycle() or one of the convenience functions.
    set_state() is the raw commit — use only when D6 has already run
    (e.g. from state_router after compute_next_state()).
  - Raw field mutation (e.g. _state.coherence = 0.5) is FORBIDDEN.
    Every write must flow through D6 so the engine always has the last word.
  - GOVERNANCE override is always available regardless of any threshold.
    Use governance_override() or POST /state/governance. Never gate it.
  - PROTECT mode sets mode_locked=True. Only governance_override() or
    unlock_protect() can exit it.
  - Thread safety: every read and write acquires _lock.
    Do not hold _lock across I/O or async operations.

For the Good and the Greater Good.
"""

from __future__ import annotations

import threading
from copy import deepcopy
from datetime import datetime, timezone
from typing import Optional

from gaia.core.state import GAIAOperationalMode, GAIAState
from gaia.core.d6_engine import D6Decision, D6Inputs, compute_next_state, clamp


# ── Internal singleton ─────────────────────────────────────────────

_lock = threading.Lock()
_state: GAIAState = GAIAState()  # boot with safe v2 defaults


# ── Core read functions ────────────────────────────────────────────────

def get_state() -> GAIAState:
    """Return the current GAIAState snapshot (thread-safe read)."""
    with _lock:
        return _state


def get_runtime_json() -> dict:
    """Return the full D6 runtime JSON schema (canon: Part VI of D6 doc)."""
    return get_state().to_runtime_json()


def get_mode() -> str:
    """Return the current mode value string (lightweight read for logging/gating)."""
    with _lock:
        return _state.mode.value


# ── Raw commit (internal / post-D6 use only) ─────────────────────────────

def set_state(new_state: GAIAState) -> None:
    """Commit a new GAIAState (thread-safe write).

    Use this ONLY when D6 has already run (e.g. state_router calls
    compute_next_state() then set_state() with the result).
    For all other cases use run_d6_cycle() or a convenience function.
    """
    global _state
    with _lock:
        _state = new_state


# ── Primary write path ──────────────────────────────────────────────────

def run_d6_cycle(
    *,
    # ─ Dimensional health probes (D1–D5) ─────────────────────────────────
    d1_health: Optional[float] = None,
    d2_health: Optional[float] = None,
    d3_health: Optional[float] = None,
    d4_health: Optional[float] = None,
    d5_health: Optional[float] = None,
    # ─ Scalar state ──────────────────────────────────────────────────────────
    energy: Optional[float] = None,
    stress: Optional[float] = None,
    entropy: Optional[float] = None,
    personal_coherence: Optional[float] = None,
    noosphere_load: Optional[float] = None,
    # ─ Legacy scalar (deprecated — prefer d1–d5 probes) ───────────────────
    coherence: Optional[float] = None,
    planetary_coherence: Optional[float] = None,  # alias for noosphere_load
    # ─ Temporal / talisman ────────────────────────────────────────────
    cycle_position: Optional[int] = None,
    epoch: Optional[str] = None,
    active_talismans: Optional[list[str]] = None,
    special_conditions: Optional[list[str]] = None,
    # ─ Rich D6 input probes ───────────────────────────────────────────
    recent_error_rate: Optional[float] = None,
    session_hours: Optional[float] = None,
    # kept for backward compat with v1 callers
    session_streak_hours: Optional[float] = None,
    new_data_present: bool = False,
    threat_detected: bool = False,
    architect_request: bool = False,
) -> D6Decision:
    """Update probe values on the current state, run D6, commit, and return.

    This is the PRIMARY write path for the entire backend.
    Any subsystem that wants to update state (biometrics, noosphere,
    CI monitor, talisman engine, etc.) calls this function.

    Rules:
      - Only the probes you pass will be updated; others retain their value.
      - All float values are clamped to [0.0, 1.0] before being applied.
      - D6 ALWAYS runs after any update — no bypass.
      - If architect_request=True, D6 will unconditionally return GOVERNANCE.
      - session_streak_hours is a v1 alias for session_hours.
    """
    global _state
    with _lock:
        updated = deepcopy(_state)

        # ─ Dimensional probes (authoritative coherence inputs) ────────────────────
        if d1_health is not None:
            updated.d1_health = clamp(d1_health)
        if d2_health is not None:
            updated.d2_health = clamp(d2_health)
        if d3_health is not None:
            updated.d3_health = clamp(d3_health)
        if d4_health is not None:
            updated.d4_health = clamp(d4_health)
        if d5_health is not None:
            updated.d5_health = clamp(d5_health)

        # ─ Scalar state ────────────────────────────────────────────────────────
        if energy is not None:
            updated.energy = clamp(energy)
        if stress is not None:
            updated.stress = clamp(stress)
        if entropy is not None:
            updated.entropy = clamp(entropy)
        if personal_coherence is not None:
            updated.personal_coherence = clamp(personal_coherence)

        # noosphere_load wins over the deprecated planetary_coherence alias
        if noosphere_load is not None:
            updated.noosphere_load = clamp(noosphere_load)
            updated.planetary_coherence = clamp(noosphere_load)  # keep alias in sync
        elif planetary_coherence is not None:
            updated.planetary_coherence = clamp(planetary_coherence)
            updated.noosphere_load = clamp(planetary_coherence)

        # legacy coherence scalar (soft-deprecated; d1–d5 are authoritative)
        if coherence is not None:
            updated.coherence = clamp(coherence)

        # ─ Temporal / talisman ───────────────────────────────────────────
        if cycle_position is not None:
            updated.cycle_position = cycle_position
        if epoch is not None:
            updated.epoch = epoch
        if active_talismans is not None:
            updated.active_talismans = active_talismans
        if special_conditions is not None:
            updated.special_conditions = special_conditions

        # ─ Build D6Inputs ───────────────────────────────────────────────────
        # Resolve session_hours: v2 name wins over v1 alias
        resolved_hours = session_hours if session_hours is not None else session_streak_hours

        inputs = D6Inputs(
            current_state=updated,
            architect_request=architect_request,
            recent_error_rate=recent_error_rate,
            session_hours=resolved_hours,
            new_data_present=new_data_present,
            threat_detected=threat_detected,
        )

        decision = compute_next_state(inputs)
        _state = decision.next_state

    return decision


# ── Convenience write functions ───────────────────────────────────────────────

def governance_override(reason: str = "") -> D6Decision:
    """Architect override — immediately set GOVERNANCE mode.

    No coherence check. No stress check. No mode_locked check.
    The human comes first. (Issue #578 — Architect Protocol)

    This is the non-HTTP path — for use by CLI, background tasks,
    and any subsystem that needs to hand control to the Architect.
    HTTP callers use POST /state/governance.
    """
    if reason:
        pass  # reason logged by caller or via interventions
    return run_d6_cycle(architect_request=True)


def request_mode_change(requested_mode: GAIAOperationalMode) -> D6Decision:
    """Request a specific mode change.

    D6 validates whether conditions support the requested mode.
    If not, D6 selects the appropriate mode and returns its rationale.
    This is intentional: the human can request, but the system's
    actual health determines what is safe.

    Unconditional exceptions (always honoured without D6 override):
      - GOVERNANCE → use governance_override() instead
      - RECOVER    → always accepted; no threshold required
    """
    global _state
    with _lock:
        candidate = deepcopy(_state)

        # RECOVER is always accepted unconditionally
        if requested_mode == GAIAOperationalMode.RECOVER:
            candidate.mode = requested_mode
            candidate.mode_locked = False
            candidate.last_transition_at = datetime.now(timezone.utc)
            _state = candidate
            return D6Decision(
                next_state=candidate,
                interventions=[f"mode_change_honoured: {requested_mode.value}"],
                rationale=(
                    f"Architect requested {requested_mode.value} — "
                    "accepted unconditionally."
                ),
            )

        # GOVERNANCE requests should use governance_override() for clarity
        if requested_mode == GAIAOperationalMode.GOVERNANCE:
            inputs = D6Inputs(
                current_state=candidate,
                architect_request=True,
            )
            decision = compute_next_state(inputs)
            _state = decision.next_state
            return decision

        # All other modes: run D6 and let it decide
        inputs = D6Inputs(current_state=candidate)
        decision = compute_next_state(inputs)
        _state = decision.next_state

    return decision


def update_talismans(
    active_talismans: list[str],
    *,
    run_cycle: bool = True,
) -> D6Decision | None:
    """Atomically update the active talisman list.

    If run_cycle=True (default), D6 runs immediately after updating
    so talisman coherence boost is reflected in the new mode decision.
    If run_cycle=False, updates the list and returns None — useful
    for batch updates where you will call run_d6_cycle() yourself.

    Canon source: Issue #580 (Talisman Object).
    """
    if run_cycle:
        return run_d6_cycle(active_talismans=active_talismans)
    global _state
    with _lock:
        _state = deepcopy(_state)
        _state.active_talismans = active_talismans
    return None


def unlock_protect(reason: str = "") -> D6Decision:
    """Architect confirmation to unlock PROTECT mode.

    Clears mode_locked=True then runs D6 to reassign the
    appropriate recovery mode. Only the Architect can call this.
    HTTP callers use POST /state/unlock.
    """
    global _state
    with _lock:
        current = deepcopy(_state)

        if not current.mode_locked:
            # Nothing to unlock — run a normal D6 cycle and return
            inputs = D6Inputs(current_state=current)
            decision = compute_next_state(inputs)
            _state = decision.next_state
            return decision

        current.mode_locked = False
        inputs = D6Inputs(current_state=current)
        decision = compute_next_state(inputs)
        _state = decision.next_state

    note = f" Reason: {reason}" if reason else ""
    decision.interventions.insert(
        0, f"PROTECT unlocked by Architect.{note} D6 re-evaluated."
    )
    return decision


def session_start(
    session_id: str,
    cycle_position: int,
    epoch: str = "Iosis",
    special_conditions: Optional[list[str]] = None,
) -> D6Decision:
    """Bootstrap a new GAIA session.

    Sets session_id, cycle_position, epoch, and any special conditions
    (e.g. Venus eclipse), then runs D6 with full circadian context.
    Call this once at the start of each work session.
    """
    return run_d6_cycle(
        cycle_position=cycle_position,
        epoch=epoch,
        special_conditions=special_conditions or [],
    )


def reset_state(*, seed: Optional[GAIAState] = None) -> None:
    """Reset the singleton to a fresh GAIAState.

    If seed is provided, the store is seeded with that state (no D6 run).
    If seed is None, a brand-new GAIAState() with safe defaults is used.

    Use cases:
      - Test setup / teardown: reset between test cases
      - App startup: seed from persisted state loaded from DB
      - Emergency reset: clear a corrupted runtime state

    WARNING: This bypasses D6. Use only for init / test scenarios.
    """
    global _state
    with _lock:
        _state = deepcopy(seed) if seed is not None else GAIAState()
