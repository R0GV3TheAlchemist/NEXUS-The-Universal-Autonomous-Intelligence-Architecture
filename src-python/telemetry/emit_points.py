"""Convenience emit-point factories.

Each GAIA engine imports the factory it needs and calls it with minimal
boilerplate. Keeps emit sites clean while keeping all schema knowledge here.

Usage example (Synergy Orchestrator):

    from telemetry.emit_points import emit_job_started, emit_job_completed

    await emit_job_started(telemetry, session_id, skill_id="research_desk", intent_class="research")
    # ... do work ...
    await emit_job_completed(telemetry, session_id, skill_id="research_desk",
                             duration_ms=420, dq_score=0.91)
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from .collector import TelemetryCollector
from .models import TelemetryEvent


async def emit_job_started(
    telemetry: TelemetryCollector,
    session_id: str,
    skill_id: str,
    intent_class: Optional[str] = None,
    biometric_context: Optional[str] = None,
    planetary_context: Optional[str] = None,
) -> None:
    await telemetry.emit(TelemetryEvent(
        session_id=session_id,
        source="synergy_orchestrator",
        event_type="job_started",
        skill_id=skill_id,
        intent_class=intent_class,
        biometric_context=biometric_context,
        planetary_context=planetary_context,
        canon_refs=["C05", "C30"],
    ))


async def emit_job_completed(
    telemetry: TelemetryCollector,
    session_id: str,
    skill_id: str,
    duration_ms: int,
    dq_score: Optional[float] = None,
    degraded: bool = False,
    fallback_mode: Optional[str] = None,
    intent_class: Optional[str] = None,
    engine_count: int = 1,
    biometric_context: Optional[str] = None,
    planetary_context: Optional[str] = None,
) -> None:
    await telemetry.emit(TelemetryEvent(
        session_id=session_id,
        source="synergy_orchestrator",
        event_type="job_completed",
        skill_id=skill_id,
        intent_class=intent_class,
        duration_ms=duration_ms,
        dq_score=dq_score,
        degraded=degraded,
        fallback_mode=fallback_mode,
        biometric_context=biometric_context,
        planetary_context=planetary_context,
        tags=[f"engines:{engine_count}"],
        canon_refs=["C05"],
    ))


async def emit_job_failed(
    telemetry: TelemetryCollector,
    session_id: str,
    skill_id: str,
    duration_ms: int,
    error_summary: str,
    intent_class: Optional[str] = None,
) -> None:
    await telemetry.emit(TelemetryEvent(
        session_id=session_id,
        source="synergy_orchestrator",
        event_type="job_failed",
        skill_id=skill_id,
        intent_class=intent_class,
        duration_ms=duration_ms,
        output_summary=error_summary,
        canon_refs=["C30"],
    ))


async def emit_sandbox_event(
    telemetry: TelemetryCollector,
    session_id: str,
    event_type: str,          # "sandbox_started" | "sandbox_violation" | "sandbox_completed"
    skill_id: Optional[str] = None,
    risk_tier: Optional[str] = None,
    trust_tier: Optional[str] = None,
    duration_ms: int = 0,
    output_summary: str = "",
) -> None:
    await telemetry.emit(TelemetryEvent(
        session_id=session_id,
        source="sandbox",
        event_type=event_type,
        skill_id=skill_id,
        risk_tier=risk_tier,
        trust_tier=trust_tier,
        duration_ms=duration_ms,
        output_summary=output_summary,
        canon_refs=["C50", "C30"],
    ))


async def emit_skill_invoked(
    telemetry: TelemetryCollector,
    session_id: str,
    skill_id: str,
    trust_tier: str,
    risk_tier: Optional[str] = None,
    duration_ms: int = 0,
) -> None:
    await telemetry.emit(TelemetryEvent(
        session_id=session_id,
        source="skill_trust",
        event_type="skill_invoked",
        skill_id=skill_id,
        trust_tier=trust_tier,
        risk_tier=risk_tier,
        duration_ms=duration_ms,
        canon_refs=["C05"],
    ))


async def emit_healing_event(
    telemetry: TelemetryCollector,
    session_id: str,
    skill_id: str,
    fallback_mode: str,
    attempt_number: int,
    degraded: bool = True,
) -> None:
    """Emitted by Self-Healing Engine (Issue #187)."""
    await telemetry.emit(TelemetryEvent(
        session_id=session_id,
        source="healing",
        event_type="fallback_used",
        skill_id=skill_id,
        degraded=degraded,
        fallback_mode=fallback_mode,
        input_summary=f"attempt={attempt_number}",
        canon_refs=["C30", "C01"],
    ))


async def emit_action_gate(
    telemetry: TelemetryCollector,
    session_id: str,
    skill_id: str,
    risk_tier: str,
    trust_tier: Optional[str] = None,
    user_approved: Optional[bool] = None,
) -> None:
    outcome = "approved" if user_approved else "pending" if user_approved is None else "denied"
    await telemetry.emit(TelemetryEvent(
        session_id=session_id,
        source="action_gate",
        event_type="action_gate_triggered",
        skill_id=skill_id,
        risk_tier=risk_tier,
        trust_tier=trust_tier,
        output_summary=outcome,
        canon_refs=["C50", "C01"],
    ))


async def emit_biometric_change(
    telemetry: TelemetryCollector,
    session_id: str,
    coherence_label: str,
) -> None:
    await telemetry.emit(TelemetryEvent(
        session_id=session_id,
        source="biometric",
        event_type="context_change",
        biometric_context=coherence_label,
        canon_refs=["C29"],
    ))


async def emit_planetary_change(
    telemetry: TelemetryCollector,
    session_id: str,
    planetary_label: str,
) -> None:
    await telemetry.emit(TelemetryEvent(
        session_id=session_id,
        source="planetary",
        event_type="context_change",
        planetary_context=planetary_label,
        canon_refs=["C44"],
    ))
