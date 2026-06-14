"""
core/gaian_runtime_extension.py
GAIA Runtime Extension Registry

Provides a clean plugin protocol so new subsystems (Ley Line Matrix,
future engines) can self-register into GAIANRuntime without ever
modifying gaian_runtime.py again.

Each extension implements RuntimeExtension and calls register_extension()
at import time. GAIANRuntime iterates _REGISTRY in __init__, process(),
_assemble(), and get_status().

Extension lifecycle per turn:
  1. init(runtime)        → called once in __init__, returns subsystem instance
  2. emit(instance, ctx)  → called every process() turn, returns Optional[dict]
  3. build_block(status)  → called in _assemble() if status is not None, returns str
  4. status(instance)     → called in get_status(), returns dict

Sprint: Ley Line Matrix ◈ — June 14, 2026
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

logger = logging.getLogger("gaia.runtime_extension")


# ── ProcessContext ───────────────────────────────────────────────────────────────────────────────
# A lightweight bundle of the live per-turn values an extension needs.
# Passed to emit() each turn. Add fields here as the runtime grows —
# extensions only consume what they need.

@dataclass
class ProcessContext:
    """Live per-turn values passed to every extension's emit()."""
    gaian_name:           str
    user_message:         str
    coherence_phi:        float
    bond_depth:           float
    dominant_hz:          float
    synergy_stage:        str
    lci:                  float
    pneuma_flow:          float
    spiritu_stage:        str
    mc_stage:             str
    individuation_phase:  str
    noosphere_health:     float
    quantum_dominant:     str
    quantum_purity:       float
    extra:                dict[str, Any] = field(default_factory=dict)


# ── RuntimeExtension protocol ─────────────────────────────────────────────────────

@dataclass
class RuntimeExtension:
    """
    Self-contained descriptor for one optional GAIA runtime subsystem.

    Attributes
    ----------
    name        : str
        Canonical snake_case key used in state_snapshot, RuntimeResult,
        get_status(), and logger messages.  e.g. "ley_line"
    symbol      : str
        Unicode glyph shown in log lines.  e.g. "◈"
    init        : Callable[[Any], Any]
        Called once during GAIANRuntime.__init__.
        Receives the runtime instance, returns the subsystem object
        (stored as runtime._ext_instances[name]).
        Must not raise — wrap risky init in try/except inside the callable.
    emit        : Callable[[Any, ProcessContext], Optional[dict]]
        Called every process() turn.
        Args: (subsystem_instance, ctx: ProcessContext)
        Returns a JSON-serialisable dict on success, None on skip/error.
    build_block : Callable[[dict], str]
        Called in _assemble() when emit() returned a non-None dict.
        Returns the system-prompt block string.
    status      : Callable[[Any], dict]
        Called in get_status().
        Args: (subsystem_instance,)
        Returns a JSON-serialisable status dict.
    audit_keys  : Callable[[Optional[dict]], dict]
        Called in process() to extract keys for the STATE_SNAPSHOT audit event.
        Args: (emit_result,)  — may be None.
        Returns a flat dict of scalar audit values.
    """
    name:        str
    symbol:      str
    init:        Callable[[Any], Any]
    emit:        Callable[[Any, "ProcessContext"], Optional[dict]]
    build_block: Callable[[dict], str]
    status:      Callable[[Any], dict]
    audit_keys:  Callable[[Optional[dict]], dict] = field(
        default_factory=lambda: (lambda result: {})
    )


# ── Global registry ─────────────────────────────────────────────────────────────────────

_REGISTRY: list[RuntimeExtension] = []


def register_extension(ext: RuntimeExtension) -> None:
    """Register a RuntimeExtension. Called at module import time by each subsystem."""
    for existing in _REGISTRY:
        if existing.name == ext.name:
            logger.warning(
                "[ExtensionRegistry] Extension '%s' already registered — skipping duplicate.",
                ext.name,
            )
            return
    _REGISTRY.append(ext)
    logger.info(
        "[ExtensionRegistry] ✓ Registered extension: '%s' %s", ext.name, ext.symbol
    )


def get_registry() -> list[RuntimeExtension]:
    """Return the current list of registered extensions (read-only copy)."""
    return list(_REGISTRY)
