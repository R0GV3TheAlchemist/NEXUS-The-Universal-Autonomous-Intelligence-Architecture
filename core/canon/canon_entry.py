"""
Canon Entry — atomic unit of knowledge within the GAIA Canon system.

Provides:
  - CanonEntry       : main dataclass
  - CanonEntryError  : exception class
  - RegisterSignal   : enum for registration lifecycle signals
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class RegisterSignal(str, Enum):
    """Lifecycle signal for canon entry registration."""

    PENDING = "pending"
    REGISTERED = "registered"
    UPDATED = "updated"
    DEPRECATED = "deprecated"
    REJECTED = "rejected"


class CanonEntryError(Exception):
    """Raised when a CanonEntry operation fails."""


@dataclass
class CanonEntry:
    """An atomic knowledge record in the GAIA Canon."""

    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    body: str = ""
    tags: List[str] = field(default_factory=list)
    source: str = ""
    signal: RegisterSignal = RegisterSignal.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------ #
    #  Helpers                                                             #
    # ------------------------------------------------------------------ #

    def register(self) -> None:
        if self.signal not in (RegisterSignal.PENDING, RegisterSignal.REJECTED):
            raise CanonEntryError(
                f"Cannot register entry in state {self.signal!r}"
            )
        self.signal = RegisterSignal.REGISTERED
        self.updated_at = datetime.now(timezone.utc)

    def update(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise CanonEntryError(f"CanonEntry has no field {key!r}")
            setattr(self, key, value)
        self.version += 1
        self.updated_at = datetime.now(timezone.utc)
        self.signal = RegisterSignal.UPDATED

    def deprecate(self) -> None:
        self.signal = RegisterSignal.DEPRECATED
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "title": self.title,
            "body": self.body,
            "tags": self.tags,
            "source": self.source,
            "signal": self.signal.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "version": self.version,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CanonEntry":
        signal_raw = data.get("signal", RegisterSignal.PENDING.value)
        try:
            signal = RegisterSignal(signal_raw)
        except ValueError:
            signal = RegisterSignal.PENDING
        return cls(
            entry_id=data.get("entry_id", str(uuid.uuid4())),
            title=data.get("title", ""),
            body=data.get("body", ""),
            tags=data.get("tags", []),
            source=data.get("source", ""),
            signal=signal,
            version=data.get("version", 1),
            metadata=data.get("metadata", {}),
        )
