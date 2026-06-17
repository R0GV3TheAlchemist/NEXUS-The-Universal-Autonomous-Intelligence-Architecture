# core/memory/sovereignty.py
# E712 and E741 fixes applied
# (Full file reproduced with targeted fixes only — all other logic unchanged)

from __future__ import annotations

from sqlalchemy.orm import Session
from gaia.db.models import MemoryRecord, AuditLog


def export_records(db: Session, user_id_hash: str, space_id: str | None = None):
    """
    Export memory records that are flagged as exportable for a given user.
    E712 fix: SQLAlchemy boolean column comparisons use `is True` not `== True`.
    """
    q = db.query(MemoryRecord).filter(
        MemoryRecord.user_id_hash == user_id_hash,
        MemoryRecord.exportable.is_(True),
    )
    if space_id:
        q = q.filter(MemoryRecord.space_id == space_id)
    return q.all()


def deletable_records(db: Session, user_id_hash: str):
    """
    Return all memory records that the user can delete.
    E712 fix: use .is_(True) for SQLAlchemy boolean filter.
    """
    records = db.query(MemoryRecord).filter(
        MemoryRecord.user_id_hash == user_id_hash,
        MemoryRecord.user_deletable.is_(True),
    ).all()
    return records


def get_audit_log(db: Session, user_id_hash: str) -> list[dict]:
    """
    Return audit log entries for a user.
    E741 fix: renamed loop variable `l` → `log_entry`.
    """
    logs = db.query(AuditLog).filter(
        AuditLog.user_id_hash == user_id_hash,
    ).all()
    return [
        {
            "id": log_entry.id,
            "action": log_entry.action,
            "details": log_entry.details,
        }
        for log_entry in logs
    ]


class SovereigntyLayer:
    """Canon C17: Sovereign memory access control wrapper."""

    def __init__(self, db: Session):
        self.db = db

    def export(self, user_id_hash: str, space_id: str | None = None):
        return export_records(self.db, user_id_hash, space_id)

    def deletable(self, user_id_hash: str):
        return deletable_records(self.db, user_id_hash)

    def audit_log(self, user_id_hash: str) -> list[dict]:
        return get_audit_log(self.db, user_id_hash)
