# Copyright © 2025–2026 Kyle Alexander Steen. All rights reserved. AGPL-3.0.
"""
core.c27 — C27 GAIAN Stewardship & Lifecycle

Canon: C27_GAIAN_Stewardship_and_Lifecycle.md
Issue: #768

Modules:
    lifecycle        — GAIANLifecycleState enum, LifecycleStateMachine
    audit_log        — AuditLogWriter, AuditLogReader, AuditLogIntegrityVerifier
    stewardship      — StewardshipBond, GAIANRights, StewardSuccessionIntent
    adoption         — AdoptionQueueEntry, AdoptionEligibilityChecker, AdoptionTimeoutDaemon
    sentinel_checks  — C27SentinelChecks (CHK-001 through CHK-007)
    retirement       — RetirementEngine, RetirementIntent
    rbac             — RBACEnforcer, IsolationBoundary, CrossGAIANDataShareAuthorization
"""

from core.c27.lifecycle import (
    GAIANLifecycleState,
    LifecycleTrigger,
    LifecycleStateMachine,
    ProhibitedTransitionError,
)
from core.c27.audit_log import AuditLogEntry, AuditLogWriter, AuditLogReader
from core.c27.stewardship import StewardshipBond, GAIANRights, StewardSuccessionIntent
from core.c27.adoption import AdoptionQueueEntry, AdoptionTimeoutDaemon
from core.c27.sentinel_checks import C27SentinelChecks, SentinelFinding, SentinelSeverity
from core.c27.retirement import RetirementEngine, RetirementCondition
from core.c27.rbac import C27Role, RBACEnforcer, IsolationBoundary

__all__ = [
    "GAIANLifecycleState",
    "LifecycleTrigger",
    "LifecycleStateMachine",
    "ProhibitedTransitionError",
    "AuditLogEntry",
    "AuditLogWriter",
    "AuditLogReader",
    "StewardshipBond",
    "GAIANRights",
    "StewardSuccessionIntent",
    "AdoptionQueueEntry",
    "AdoptionTimeoutDaemon",
    "C27SentinelChecks",
    "SentinelFinding",
    "SentinelSeverity",
    "RetirementEngine",
    "RetirementCondition",
    "C27Role",
    "RBACEnforcer",
    "IsolationBoundary",
]
