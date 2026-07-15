"""GAIAMode — canonical GAIA operating mode enum.

Canon References: C03 (Ontology Runtime), C14 (OS and World Fabric Spec)
Issue: D6 Engine (GAIAMode missing members)

GAIAMode describes the *system-level operating posture* of a GAIA instance.
This is distinct from AlchemicalStage (which tracks entity lifecycle) and
PermissionTier (which governs capability envelopes).

Rules:
  1. All D6 engine references to GAIAMode.X must exist here — never in callers.
  2. Use str mixin so GAIAMode members serialise to plain strings without .value.
  3. Never import this from anywhere except core.ontology (go through __init__).
"""
from __future__ import annotations

from enum import Enum


class GAIAMode(str, Enum):
    """System-level operating mode for a GAIA runtime instance.

    Members
    -------
    DORMANT
        System is initialised but not processing.  Default boot state.
    PRIMORDIAL
        Pre-session state; World Fabric wiring in progress.
    OBSERVE
        Passive monitoring only.  No state-changing actions permitted.
    THINK
        Internal cognition active.  No external actions permitted.
    ACT
        Full agentic loop engaged.  External actions permitted within
        the Permission Envelope.
    SENTINEL
        Elevated monitoring mode.  Triggered by anomaly detection.
    EMERGENT
        Post-threshold state where new Gaian capabilities become available.
        Requires Human Principal acknowledgement to enter.
    D6
        D6 Numerological Engine mode.  Activated by the D6 engine subsystem.
    SEALED
        Session has been sealed.  No further state changes permitted.
    """

    DORMANT = "DORMANT"
    PRIMORDIAL = "PRIMORDIAL"
    OBSERVE = "OBSERVE"
    THINK = "THINK"
    ACT = "ACT"
    SENTINEL = "SENTINEL"
    EMERGENT = "EMERGENT"
    D6 = "D6"
    SEALED = "SEALED"

    def is_active(self) -> bool:
        """Return True if the mode allows active processing."""
        return self in (GAIAMode.THINK, GAIAMode.ACT, GAIAMode.SENTINEL, GAIAMode.D6)

    def allows_external_action(self) -> bool:
        """Return True if the mode permits external (side-effect) actions."""
        return self in (GAIAMode.ACT, GAIAMode.D6)
