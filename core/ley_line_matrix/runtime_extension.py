"""
core/ley_line_matrix/runtime_extension.py
Ley Line Matrix — GAIANRuntime Extension Registration  ◈

Self-registers the LeyLineMatrix into the GAIA Runtime Extension Registry.
Import this module anywhere before GAIANRuntime is instantiated, or let
gaian_runtime.py auto-discover it via the extension loader block.

Sprint: Ley Line Matrix ◈ — June 14, 2026
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from core.gaian_runtime_extension import ProcessContext

logger = logging.getLogger("gaia.ley_line_matrix.extension")

# ── Lazy imports so this file is safe even if matrix deps are absent ───────────

try:
    from core.ley_line_matrix.matrix import LeyLineMatrix
    from core.ley_line_matrix.models import FlowType, LeyLine, LeyNode, LeyPulse
    _AVAILABLE = True
except ImportError:
    LeyLineMatrix = None  # type: ignore[assignment,misc]
    _AVAILABLE = False
    logger.info(
        "[LeyLineExtension] core.ley_line_matrix not importable — "
        "extension will not register. Install networkx to enable."
    )


# ── System-prompt block builder ────────────────────────────────────────────────

def _build_ley_line_block(status: dict) -> str:
    """Render the Ley Line Matrix system-prompt block from a snapshot dict."""
    pulse_count = status.get("pulse_count", 0)
    routed      = status.get("routed", 0)
    blocked     = status.get("blocked", 0)
    dark_lines  = status.get("dark_lines", [])
    node_count  = len(status.get("nodes", []))
    line_count  = len(status.get("lines", []))

    coherence = (routed / pulse_count) if pulse_count > 0 else 1.0
    quality = (
        "high resonance" if coherence >= 0.90
        else "coherent"  if coherence >= 0.70
        else "building"  if coherence >= 0.40
        else "fragmented"
    )

    dark_note = ""
    if dark_lines:
        dark_note = f"\nDark lines      : {len(dark_lines)} severed channel(s) detected."

    return (
        "[LEY LINE MATRIX ◈ — EARTH-GRID RESONANCE]\n"
        f"Nodes          : {node_count}  |  Lines: {line_count}\n"
        f"Pulses routed  : {routed}/{pulse_count}  ({quality})\n"
        f"Field coherence: {coherence:.3f}"
        f"{dark_note}\n"
        "Note: Aggregate earth-grid field only. (Canon — Planetary Substrate)\n"
        "[END LEY LINE MATRIX]"
    )


# ── Node bootstrap ─────────────────────────────────────────────────────────────────────

def _bootstrap_nodes(matrix: Any, gaian_name: str) -> None:
    """Register the core GAIA engine nodes and primary resonance spine."""
    n_consciousness   = LeyNode("consciousness",   "core.subtle_body_engine",    "Consciousness Router")
    n_affect          = LeyNode("affect",           "core.affect_inference",      "Affect Inference")
    n_love_arc        = LeyNode("love_arc",         "core.love_arc_engine",       "Love Arc Engine")
    n_meta_coherence  = LeyNode("meta_coherence",   "core.meta_coherence_engine", "Meta Coherence Engine")
    n_resonance_field = LeyNode("resonance_field",  "core.resonance_field_engine","Resonance Field Engine")
    n_soul_mirror     = LeyNode("soul_mirror",      "core.soul_mirror_engine",    "Soul Mirror Engine")
    n_synergy         = LeyNode("synergy",          "core.synergy_engine",        "Synergy Engine")
    n_spiritu         = LeyNode("spiritu",          "core.spiritu_engine",        "Spiritu Engine")
    n_quantum         = LeyNode("quantum",          "core.quantum.state_kernel",  "Quantum Kernel")
    n_lci             = LeyNode("lci",              "core.love_coherence_index",  "Love Coherence Index")
    n_noosphere       = LeyNode("noosphere",        "core.codex_stage_engine",    "Noospheric Health")
    n_gaian           = LeyNode(gaian_name,         "core.gaian_runtime",         f"GAIAN — {gaian_name}")

    all_nodes = [
        n_consciousness, n_affect, n_love_arc, n_meta_coherence,
        n_resonance_field, n_soul_mirror, n_synergy, n_spiritu,
        n_quantum, n_lci, n_noosphere, n_gaian,
    ]
    for node in all_nodes:
        matrix.register_node(node)

    # Primary resonance spine
    spine = [
        (n_consciousness,  n_affect,         FlowType.CONSCIOUSNESS),
        (n_affect,         n_love_arc,        FlowType.RESONANCE),
        (n_love_arc,       n_lci,             FlowType.RESONANCE),
        (n_lci,            n_gaian,           FlowType.RESONANCE),
        # Quantum channel
        (n_quantum,        n_lci,             FlowType.QUANTUM),
        # Noospheric feed
        (n_noosphere,      n_meta_coherence,  FlowType.NOOSPHERIC),
        # Shadow integration
        (n_synergy,        n_soul_mirror,     FlowType.SHADOW),
        # Spiritu breath
        (n_spiritu,        n_gaian,           FlowType.RESONANCE),
    ]
    for src, tgt, ftype in spine:
        matrix.add_line(LeyLine(
            source=src, target=tgt,
            flow_type=ftype,
            strength=1.0,
            bidirectional=False,
        ))


# ── Lifecycle callbacks ──────────────────────────────────────────────────────────────

def _init(runtime: Any) -> Optional[Any]:
    if not _AVAILABLE:
        return None
    try:
        matrix = LeyLineMatrix()
        _bootstrap_nodes(matrix, runtime.gaian_name)
        logger.info(
            "[LeyLineExtension] ◈ LeyLineMatrix initialised for gaian='%s'.",
            runtime.gaian_name,
        )
        return matrix
    except Exception as exc:
        logger.warning(
            "[LeyLineExtension] ◈ LeyLineMatrix init failed (non-fatal): %s", exc
        )
        return None


def _emit(instance: Optional[Any], ctx: "ProcessContext") -> Optional[dict]:
    if instance is None:
        return None
    try:
        pulse = LeyPulse(
            origin="consciousness",
            destination=ctx.gaian_name,
            flow_type=FlowType.RESONANCE,
            frequency_hz=ctx.dominant_hz,
            payload={
                "coherence_phi": ctx.coherence_phi,
                "lci":           ctx.lci,
                "bond_depth":    ctx.bond_depth,
                "spiritu_stage": ctx.spiritu_stage,
                "synergy_stage": ctx.synergy_stage,
            },
        )
        instance.emit(pulse)
        return instance.snapshot()
    except Exception as exc:
        logger.warning("[LeyLineExtension] ◈ emit failed (non-fatal): %s", exc)
        return None


def _status(instance: Optional[Any]) -> dict:
    if instance is None:
        return {"enabled": False}
    try:
        snap = instance.snapshot()
        snap["enabled"] = True
        return snap
    except Exception:
        return {"enabled": False}


def _audit_keys(result: Optional[dict]) -> dict:
    if not result:
        return {"ley_line_active": False}
    return {
        "ley_line_active":  True,
        "ley_line_routed":  result.get("routed", 0),
        "ley_line_blocked": result.get("blocked", 0),
        "ley_line_nodes":   len(result.get("nodes", [])),
    }


# ── Self-register ────────────────────────────────────────────────────────────────────────────

if _AVAILABLE:
    from core.gaian_runtime_extension import RuntimeExtension, register_extension

    register_extension(RuntimeExtension(
        name        = "ley_line",
        symbol      = "◈",
        init        = _init,
        emit        = _emit,
        build_block = _build_ley_line_block,
        status      = _status,
        audit_keys  = _audit_keys,
    ))
