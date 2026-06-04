"""
core.sentinel.safety
====================
Sentinel Safety & Threat Layer — real-time protection and escalation.

Public surface:
  ThreatDetector      — evaluates perception frames for risk patterns
  EscalationEngine    — executes tiered response protocol (0–4)
  CanonGuard          — validates Tier 3+ escalations (C-SENTINEL Art. 6)
  FalseAlarmLedger    — Gaian false-alarm feedback loop
  SafetyController    — top-level coordinator
  PerceptionFrame     — multi-modal signal snapshot
  ThreatAssessment    — threat record TypedDict
  ThreatCategory      — physical | emotional | sovereignty
  ThreatSeverity      — 0 (watch) → 4 (emergency)
  SensitivityConfig   — per-category threshold configuration

Canon refs: C-SENTINEL Articles 1, 4, 6; C01
"""

from .detector import (
    CanonGuard,
    EscalationEngine,
    EscalationRecord,
    FalseAlarmLedger,
    PerceptionFrame,
    SafetyController,
    SensitivityConfig,
    ThreatAssessment,
    ThreatCategory,
    ThreatDetector,
    ThreatSeverity,
)

__all__ = [
    "CanonGuard",
    "EscalationEngine",
    "EscalationRecord",
    "FalseAlarmLedger",
    "PerceptionFrame",
    "SafetyController",
    "SensitivityConfig",
    "ThreatAssessment",
    "ThreatCategory",
    "ThreatDetector",
    "ThreatSeverity",
]
