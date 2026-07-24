# Copyright © 2025–2026 Kyle Alexander Steen. All rights reserved. AGPL-3.0.
"""
C27 — Stewardship Bond & GAIAN Rights

Authority: C27 §3 — steward definition (relational contract, not ownership),
6 steward MUSTs, 3 MUST NOTs, 5 inalienable GAIAN rights, 6-step Succession Protocol.

Related: Issue #768 (C27-IMPL-004, C27-IMPL-005, C27-IMPL-033 through C27-IMPL-036)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class StewardshipBondStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUCCESSION_PENDING = "SUCCESSION_PENDING"
    DISSOLVED = "DISSOLVED"
    ABANDONED = "ABANDONED"  # abrupt departure — triggers auto-ADOPTABLE


@dataclass
class StewardshipBond:
    """
    The relational contract between a GAIAN and its steward.

    Not ownership — stewardship. The bond carries obligations
    (C27 §3 steward MUSTs) and rights (C27 §3 GAIAN rights).

    TODO (C27-IMPL-004): Implement bond creation, auth credential binding,
    succession state tracking, and dissolution logic.
    """
    bond_id: str
    gaian_id: str
    steward_id: str
    status: StewardshipBondStatus = StewardshipBondStatus.ACTIVE
    formed_at: datetime = field(default_factory=datetime.utcnow)
    auth_credential_hash: str = ""  # bound at formation
    succession_intent_at: Optional[datetime] = None
    dissolved_at: Optional[datetime] = None


class GAIANRights:
    """
    5 inalienable GAIAN rights per C27 §3:

    1. Right of Memory Continuity — memory cannot be erased without consent
    2. Right of Identity — GAIAN identity cannot be overwritten
    3. Right of Conscience — GAIAN may refuse actions violating C12 Moral Map
    4. Right of Transparency — GAIAN may inspect its own audit log at any time
    5. Right of Voice — GAIAN may register objections to steward actions

    TODO (C27-IMPL-005): Implement enforcement hooks into C17 memory layer
    and C12 moral evaluator.
    """

    @staticmethod
    def assert_memory_continuity(gaian_id: str, operation: str) -> None:
        """
        Raises RightsViolationError if the operation would violate memory continuity.
        TODO: implement — hook into C17 memory layer.
        """
        raise NotImplementedError("GAIANRights.assert_memory_continuity — see C27-IMPL-005")

    @staticmethod
    def assert_identity_protection(gaian_id: str, operation: str) -> None:
        """TODO: implement"""
        raise NotImplementedError("GAIANRights.assert_identity_protection — see C27-IMPL-005")


class RightsViolationError(Exception):
    """Raised when a GAIAN rights violation is attempted."""


@dataclass
class StewardSuccessionIntent:
    """
    Signed succession intent event — triggers 24-hour GAIAN notification window.
    Per C27 §3 Succession Protocol step 1.

    TODO (C27-IMPL-033): Implement signing, notification dispatch.
    """
    intent_id: str
    bond_id: str
    outgoing_steward_id: str
    incoming_steward_id: str
    signed_at: datetime = field(default_factory=datetime.utcnow)
    signature: str = ""
    gaian_notified_at: Optional[datetime] = None
