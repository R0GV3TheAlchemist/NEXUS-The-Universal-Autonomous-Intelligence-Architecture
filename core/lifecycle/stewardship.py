"""
core/lifecycle/stewardship.py
C27 §3 — GAIAN Stewardship Model

Defines:
  - StewardRole      : roles a steward may hold
  - StewardshipBond  : the active bond between a GAIAN and a steward
  - StewardshipRegistry : manages creation, transfer, and succession of bonds

Authority: C27 v1.0.0 (2026-07-13)
Cross-refs: C15, C17, C23
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# §3.1  Steward Roles
# ---------------------------------------------------------------------------

class StewardRole(str, Enum):
    """Roles a steward may hold over a GAIAN (C27 §3.1)."""

    PRIMARY    = "PRIMARY"     # Full stewardship accountability
    SECONDARY  = "SECONDARY"   # Delegated oversight; no unilateral retirement
    GUARDIAN   = "GUARDIAN"    # Emergency / protective role (e.g. legal guardian)
    CUSTODIAN  = "CUSTODIAN"   # Temporary caretaker during ADOPTABLE state
    OBSERVER   = "OBSERVER"    # Read-only monitoring; no lifecycle authority


# ---------------------------------------------------------------------------
# §3.2  Stewardship Bond
# ---------------------------------------------------------------------------

@dataclass
class StewardshipBond:
    """
    Represents the binding relationship between a steward and a GAIAN.

    A bond is created at BORN and remains active until:
      - The steward formally releases it (C27 §3.4 voluntary release)
      - The system determines the steward is unreachable (C27 §3.5)
      - The GAIAN is RETIRED or ARCHIVED
    """

    bond_id:       str = field(default_factory=lambda: str(uuid.uuid4()))
    gaian_id:      str = ""
    steward_id:    str = ""
    role:          StewardRole = StewardRole.PRIMARY
    created_at:    datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    released_at:   Optional[datetime] = None
    release_reason: Optional[str] = None

    # Succession: if this bond is released, who takes over?
    successor_steward_id: Optional[str] = None

    @property
    def is_active(self) -> bool:
        return self.released_at is None

    def release(
        self,
        reason: str,
        successor_steward_id: Optional[str] = None,
    ) -> None:
        """
        Formally releases this bond.
        Sets released_at, captures reason and optional successor.
        """
        if not self.is_active:
            raise ValueError(f"Bond {self.bond_id} is already released.")
        self.released_at          = datetime.now(timezone.utc)
        self.release_reason       = reason
        self.successor_steward_id = successor_steward_id

    def to_dict(self) -> dict:
        return {
            "bond_id":              self.bond_id,
            "gaian_id":             self.gaian_id,
            "steward_id":           self.steward_id,
            "role":                 self.role.value,
            "created_at":           self.created_at.isoformat(),
            "released_at":          self.released_at.isoformat() if self.released_at else None,
            "release_reason":       self.release_reason,
            "successor_steward_id": self.successor_steward_id,
        }


# ---------------------------------------------------------------------------
# §3.3  Stewardship Registry
# ---------------------------------------------------------------------------

class StewardshipRegistry:
    """
    In-process stewardship registry.

    Manages the lifecycle of StewardshipBond objects for all GAIANs.
    In production this should delegate to a persistent store (C17/C23);
    this class provides the authoritative in-memory interface.
    """

    def __init__(self) -> None:
        # gaian_id → list of all bonds (active + historical)
        self._bonds: Dict[str, List[StewardshipBond]] = {}

    # ------------------------------------------------------------------
    # Bond creation
    # ------------------------------------------------------------------

    def create_bond(
        self,
        gaian_id:   str,
        steward_id: str,
        role:       StewardRole = StewardRole.PRIMARY,
    ) -> StewardshipBond:
        """
        Creates and registers a new stewardship bond.
        Raises ValueError if an active PRIMARY bond already exists
        (a GAIAN may only have one PRIMARY steward at a time — C27 §3.2).
        """
        if role == StewardRole.PRIMARY:
            existing = self.get_active_bond(gaian_id)
            if existing and existing.role == StewardRole.PRIMARY:
                raise ValueError(
                    f"GAIAN '{gaian_id}' already has an active PRIMARY steward "
                    f"(bond {existing.bond_id}). Release it before creating a new one."
                )

        bond = StewardshipBond(
            gaian_id=gaian_id,
            steward_id=steward_id,
            role=role,
        )
        self._bonds.setdefault(gaian_id, []).append(bond)
        return bond

    # ------------------------------------------------------------------
    # Bond retrieval
    # ------------------------------------------------------------------

    def get_active_bond(
        self,
        gaian_id: str,
        role: Optional[StewardRole] = None,
    ) -> Optional[StewardshipBond]:
        """
        Returns the current active bond for a GAIAN.
        If *role* is supplied, filters to that role.
        Returns None if no matching active bond exists.
        """
        for bond in reversed(self._bonds.get(gaian_id, [])):
            if bond.is_active:
                if role is None or bond.role == role:
                    return bond
        return None

    def get_bond_history(self, gaian_id: str) -> List[StewardshipBond]:
        """Returns the full bond history (active + released) for a GAIAN."""
        return list(self._bonds.get(gaian_id, []))

    # ------------------------------------------------------------------
    # Bond release / succession (C27 §3.4, §3.5)
    # ------------------------------------------------------------------

    def release_bond(
        self,
        gaian_id:             str,
        reason:               str,
        successor_steward_id: Optional[str] = None,
    ) -> StewardshipBond:
        """
        Releases the active PRIMARY bond for a GAIAN.
        If a successor is provided, immediately creates a new PRIMARY bond
        for that steward (re-parenting / adoption — C27 §3.5).

        Returns the released bond.
        """
        bond = self.get_active_bond(gaian_id, role=StewardRole.PRIMARY)
        if bond is None:
            raise ValueError(f"No active PRIMARY bond found for GAIAN '{gaian_id}'.")

        bond.release(reason=reason, successor_steward_id=successor_steward_id)

        if successor_steward_id:
            self.create_bond(
                gaian_id=gaian_id,
                steward_id=successor_steward_id,
                role=StewardRole.PRIMARY,
            )

        return bond

    # ------------------------------------------------------------------
    # Custodian assignment (ADOPTABLE state — C27 §3.6)
    # ------------------------------------------------------------------

    def assign_custodian(
        self,
        gaian_id:     str,
        custodian_id: str,
    ) -> StewardshipBond:
        """
        Assigns a CUSTODIAN bond while the GAIAN is in ADOPTABLE state.
        Multiple custodian bonds may exist simultaneously.
        """
        return self.create_bond(
            gaian_id=gaian_id,
            steward_id=custodian_id,
            role=StewardRole.CUSTODIAN,
        )
