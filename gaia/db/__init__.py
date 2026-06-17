"""
gaia/db/__init__.py
===================
GAIA-OS Database layer public surface.

Re-exports all ORM models and helpers from gaia.db.models so that
consumers can write:

    from gaia.db import MemoryRecord, AuditLog, SessionRecord
    from gaia.db.models import CanonRef
"""

from __future__ import annotations

from gaia.db.models import (
    AuditLog,
    CanonRef,
    MemoryRecord,
    SessionRecord,
)

__all__ = [
    "AuditLog",
    "CanonRef",
    "MemoryRecord",
    "SessionRecord",
]
