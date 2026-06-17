"""
gaia/core/talisman_store.py

In-memory Talisman registry v2  —  Queue 4.

Canon anchors:
  - GAIA_TALISMAN_OBJECT.md  (sealed 2026-06-17 — Phase 1 canon)
  - Issue #580  (Talisman Object)
  - Issue #576  (GAIAState — active_talismans field)
  - Issue #568  (D6 Meta-Coherence Engine)

Design rules (v2):
  - This store is the SINGLE registry of all Talisman objects.
  - All activation / deactivation is DELEGATED to Talisman.activate() /
    Talisman.deactivate().  No manual probe arithmetic lives here.
  - get_active_talismans() is the source-of-truth bridge:
    it cross-references the in-memory store against
    state_store.get_state().active_talismans so the two are always in sync.
  - Thread-safe via _lock for all store mutations.
  - Phase 1: in-memory only.  Phase 2: persist to DB.

For the Good and the Greater Good.
"""

from __future__ import annotations

import logging
from threading import Lock
from typing import Optional

from gaia.core.talisman import (
    ActivationState,
    CoherenceFunction,
    DimensionalSignature,
    LunarPhase,
    Talisman,
    TalismanElement,
    TalismanLayer,
)

log = logging.getLogger(__name__)

_lock = Lock()
_store: dict[str, Talisman] = {}


# ---------------------------------------------------------------------------
# Read helpers
# ---------------------------------------------------------------------------

def list_talismans() -> list[Talisman]:
    """Return all talismans in the store (all activation states)."""
    with _lock:
        return list(_store.values())


def get_talisman(talisman_id: str) -> Talisman | None:
    """Return a single talisman by ID, or None if not found."""
    with _lock:
        return _store.get(talisman_id)


def get_active_talismans() -> list[Talisman]:
    """
    Return hydrated Talisman objects for every ID currently in
    GAIAState.active_talismans.

    This is the authoritative bridge between the two layers:
      - GAIAState.active_talismans  holds UUIDs (the D6 / state layer)
      - _store                       holds the full Talisman objects

    If an ID exists in GAIAState but not in _store, it is treated as
    an orphan: a warning is logged and it is skipped.  The caller
    should not normally see orphans — they indicate a store reset
    (e.g. app restart) without re-seeding state.

    Returns:
        list of Talisman objects whose activation_state == ACTIVE
        AND whose IDs appear in GAIAState.active_talismans.
    """
    from gaia.core import state_store  # lazy — avoids circular at module load

    current_state = state_store.get_state()
    active_ids: list[str] = list(current_state.active_talismans or [])

    result: list[Talisman] = []
    with _lock:
        for tid in active_ids:
            talisman = _store.get(tid)
            if talisman is None:
                log.warning(
                    "get_active_talismans: orphaned talisman ID in GAIAState: %s "
                    "(not in store — store may have been reset)",
                    tid,
                )
                continue
            result.append(talisman)

    return result


def get_talisman_summary() -> list[dict]:
    """
    Return a lightweight dict list suitable for API responses and
    front-end State HUD rendering.

    Each entry includes: id, name, dimensional_signature,
    coherence_function, activation_state, effective_boost, validated.
    """
    with _lock:
        return [
            {
                "id":                    t.id,
                "name":                  t.name,
                "dimensional_signature": t.dimensional_signature.value,
                "coherence_function":    t.coherence_function.value,
                "activation_state":      t.activation_state.value,
                "effective_boost":       t.effective_boost,
                "validated":             t.validated,
                "phase":                 t.phase,
            }
            for t in _store.values()
        ]


# ---------------------------------------------------------------------------
# Write helpers
# ---------------------------------------------------------------------------

def create_talisman(
    *,
    name:                  str,
    dimensional_signature: DimensionalSignature,
    coherence_function:    CoherenceFunction,
    # — optional Phase 1 schema fields ————————————————————————————
    archetype:             str                        = "",
    coherence_boost:       float                      = 0.05,
    stress_draw:           float                      = 0.02,
    layer:                 TalismanLayer              = TalismanLayer.DIGITAL,
    phase:                 int                        = 1,
    linked_canon:          Optional[list[str]]        = None,
    notes:                 str                        = "",
    owner:                 str                        = "",
    # — resonance metadata ———————————————————————————————————
    element:               Optional[TalismanElement]  = None,
    lunar_phase:           Optional[LunarPhase]       = None,
    frequency:             Optional[float]            = None,
) -> Talisman:
    """
    Create a new Talisman and register it in the store.

    `dimensional_signature` and `coherence_function` are required —
    they define what the talisman does and are the two non-optional
    fields from the canonical schema.

    The talisman starts with activation_state=INACTIVE and validated=False.
    Call validate_talisman() before expecting full coherence_boost.
    """
    from gaia.core.talisman import ResonanceMetadata, SovereigntyFlags

    talisman = Talisman(
        name                  = name,
        dimensional_signature  = dimensional_signature,
        coherence_function     = coherence_function,
        archetype              = archetype,
        coherence_boost        = coherence_boost,
        stress_draw            = stress_draw,
        layer                  = layer,
        phase                  = phase,
        linked_canon           = linked_canon or [],
        notes                  = notes,
        resonance_metadata     = ResonanceMetadata(
            element     = element,
            archetype   = archetype,
            lunar_phase = lunar_phase,
            frequency   = frequency,
        ),
        sovereignty_flags      = SovereigntyFlags(owner=owner),
    )

    with _lock:
        _store[talisman.id] = talisman

    log.info("talisman_store: created %r", talisman)
    return talisman


def activate_talisman(
    talisman_id: str,
    *,
    owner_id: str = "",
    run_cycle: bool = True,
) -> dict:
    """
    Activate a talisman by ID.

    Fully delegates to Talisman.activate() — no manual probe arithmetic,
    no direct state mutations.  All D6 interaction is owned by the
    Talisman object itself via state_store.update_talismans().

    Args:
        talisman_id: UUID of the talisman to activate.
        owner_id:    GAIAN owner ID for sovereignty check (Phase 2).
        run_cycle:   Whether to run D6 immediately (default True).

    Returns:
        Result dict from Talisman.activate():
        { success, talisman_id, mode, interventions, warning? }

    Raises:
        KeyError if talisman_id is not in the store.
    """
    with _lock:
        talisman = _store[talisman_id]  # raises KeyError if not found

    result = talisman.activate(owner_id=owner_id, run_cycle=run_cycle)
    log.info("talisman_store: activate %s → %s", talisman_id[:8], result)
    return result


def deactivate_talisman(
    talisman_id: str,
    *,
    run_cycle: bool = True,
) -> dict:
    """
    Deactivate a talisman by ID.

    Fully delegates to Talisman.deactivate() — removes the ID from
    GAIAState.active_talismans and triggers a D6 cycle if run_cycle=True.

    Args:
        talisman_id: UUID of the talisman to deactivate.
        run_cycle:   Whether to run D6 immediately (default True).

    Returns:
        Result dict from Talisman.deactivate():
        { success, talisman_id, mode, interventions }

    Raises:
        KeyError if talisman_id is not in the store.
    """
    with _lock:
        talisman = _store[talisman_id]

    result = talisman.deactivate(run_cycle=run_cycle)
    log.info("talisman_store: deactivate %s → %s", talisman_id[:8], result)
    return result


def validate_talisman(
    talisman_id: str,
    *,
    proof_text: str = "",
    proof_dir: str = "proofs/talismans",
) -> dict:
    """
    Validate a talisman by ID and write a proof stub.

    Delegates to Talisman.validate().  A validated talisman receives
    100 % of its coherence_boost rather than the 50 % unvalidated rate.

    Args:
        talisman_id: UUID of the talisman to validate.
        proof_text:  Optional intention statement for the proof document.
        proof_dir:   Directory for proof files (default: proofs/talismans/).

    Returns:
        Result dict from Talisman.validate():
        { success, talisman_id, proof_path, validated }

    Raises:
        KeyError if talisman_id is not in the store.
    """
    with _lock:
        talisman = _store[talisman_id]

    result = talisman.validate(proof_text=proof_text, proof_dir=proof_dir)
    log.info("talisman_store: validated %s → proof at %s", talisman_id[:8], result.get("proof_path"))
    return result


def delete_talisman(talisman_id: str) -> bool:
    """
    Remove a talisman from the store.

    If the talisman is currently ACTIVE, it is deactivated first so
    GAIAState.active_talismans stays consistent.

    Returns:
        True if removed, False if ID was not found.
    """
    with _lock:
        talisman = _store.get(talisman_id)
        if talisman is None:
            return False

    # Deactivate before deleting so state stays clean
    if talisman.activation_state == ActivationState.ACTIVE:
        talisman.deactivate(run_cycle=True)

    with _lock:
        _store.pop(talisman_id, None)

    log.info("talisman_store: deleted talisman %s", talisman_id[:8])
    return True


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

def seed_default_talismans() -> None:
    """
    Seed the store with the three default GAIA-OS talismans.

    Safe to call multiple times — no-ops if store is already populated.
    Seeds:
      1. Builder’s Flame  — D4, AMPLIFY  —  peak creative/BUILD sessions
      2. Mirror of Return  — D2, STABILIZE  —  emotional grounding, recovery
      3. Architect’s Ground  — D1-D3, GROUND  —  full lower-triad anchor
    """
    with _lock:
        if _store:
            return

    create_talisman(
        name                  = "Builder's Flame",
        dimensional_signature  = DimensionalSignature.D4,
        coherence_function     = CoherenceFunction.AMPLIFY,
        archetype              = "Builder",
        coherence_boost        = 0.07,
        stress_draw            = 0.02,
        element                = TalismanElement.FIRE,
        linked_canon           = ["C52", "GAIA_D6_META_COHERENCE_ENGINE"],
        notes                  = "Peak creative sessions, BUILD mode. Amplifies D4 generative capacity.",
    )

    create_talisman(
        name                  = "Mirror of Return",
        dimensional_signature  = DimensionalSignature.D2,
        coherence_function     = CoherenceFunction.STABILIZE,
        archetype              = "Witness",
        coherence_boost        = 0.05,
        stress_draw            = 0.01,
        element                = TalismanElement.WATER,
        linked_canon           = ["38_GAIA_Love_Doctrine", "EMBODIMENT_LAYER"],
        notes                  = "Emotional coherence anchor. Stabilises D2 above 0.75 for one D6 cycle.",
    )

    create_talisman(
        name                  = "Architect's Ground",
        dimensional_signature  = DimensionalSignature.D1_D3,
        coherence_function     = CoherenceFunction.GROUND,
        archetype              = "Alchemist",
        coherence_boost        = 0.06,
        stress_draw            = 0.02,
        element                = TalismanElement.EARTH,
        linked_canon           = ["C50", "GAIAN_LAW_CODEX", "EMBODIMENT_LAYER"],
        notes                  = "Lower-triad anchor (D1-D3). Physical grounding, mental clarity, "
                                 "emotional coherence. For late-night and high-entropy sessions.",
    )

    log.info("talisman_store: seeded 3 default talismans.")
