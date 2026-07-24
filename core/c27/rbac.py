# Copyright © 2025–2026 Kyle Alexander Steen. All rights reserved. AGPL-3.0.
"""
C27 — RBAC & Identity Isolation

Authority: C27 §6 — 5 roles, permission envelopes, identity isolation boundary,
CrossGAIANDataShare authorization, least-privilege automatic contraction.

Roles: GAIAN_SELF | STEWARD | SENTINEL | GAIA_ROOT | THIRD_PARTY

Related: Issue #768 (C27-IMPL-029 through C27-IMPL-032)
"""
from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class C27Role(str, Enum):
    GAIAN_SELF = "GAIAN_SELF"     # Always authorized for own data
    STEWARD = "STEWARD"           # Broad access, constrained by bond
    SENTINEL = "SENTINEL"         # Read-only audit access, check execution
    GAIA_ROOT = "GAIA_ROOT"       # Emergency override, critical escalation
    THIRD_PARTY = "THIRD_PARTY"   # Minimal — requires explicit authorization


# Permission envelopes per C27 §6.2 — what each role may access
ROLE_PERMISSIONS: dict[C27Role, set[str]] = {
    C27Role.GAIAN_SELF: {"read_own_memory", "read_own_audit", "update_preferences", "register_veto"},
    C27Role.STEWARD: {"read_profile", "update_state", "read_audit", "initiate_retirement", "initiate_succession"},
    C27Role.SENTINEL: {"read_audit", "read_state", "write_finding"},
    C27Role.GAIA_ROOT: {"*"},  # Full access — emergency only
    C27Role.THIRD_PARTY: {"read_public_profile"},
}


class IsolationBoundary:
    """
    Identity isolation boundary — blocks cross-GAIAN access without authorization.

    TODO (C27-IMPL-029): Implement boundary enforcement at all data access points.
    """

    def authorize(
        self,
        requestor_gaian_id: str,
        target_gaian_id: str,
        requestor_role: C27Role,
        operation: str,
    ) -> bool:
        """
        Returns True if the requestor is authorized to perform the operation
        on the target GAIAN's data.
        TODO: implement — see C27-IMPL-029
        """
        raise NotImplementedError("IsolationBoundary.authorize — see C27-IMPL-029")


@dataclass
class CrossGAIANDataShareAuthorization:
    """
    Explicit authorization for cross-GAIAN data access.
    Must be request → accept → scoped → logged → revocable.

    TODO (C27-IMPL-030): Implement full flow.
    """
    auth_id: str
    requesting_gaian_id: str
    target_gaian_id: str
    scope: list[str]  # which data fields are authorized
    granted: bool = False
    revoked: bool = False


class RBACEnforcer:
    """
    Enforces role-based access control per C27 §6.2 permission envelopes.
    Implements least-privilege automatic contraction on DORMANT/ADOPTABLE states.

    TODO (C27-IMPL-031, C27-IMPL-032): implement enforcement and contraction.
    """

    def check(
        self,
        role: C27Role,
        operation: str,
        gaian_id: Optional[str] = None,
    ) -> bool:
        """TODO: implement — see C27-IMPL-031"""
        raise NotImplementedError("RBACEnforcer.check — see C27-IMPL-031")

    def contract_permissions(self, gaian_id: str, reason: str) -> None:
        """
        Automatically reduce permissions when GAIAN enters DORMANT or ADOPTABLE,
        or when SENTINEL mandates restriction.
        TODO: C27-IMPL-032
        """
        raise NotImplementedError("RBACEnforcer.contract_permissions — see C27-IMPL-032")
