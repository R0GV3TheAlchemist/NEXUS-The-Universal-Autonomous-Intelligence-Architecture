"""
core/lifecycle/__init__.py
C27 — GAIAN Stewardship & Lifecycle  |  Phase 1 Package
"""

from .gaian_lifecycle_state import GAIANLifecycleState, LifecycleTransitionError, VALID_TRANSITIONS
from .lifecycle_manager import LifecycleManager
from .stewardship import (
    StewardRole,
    StewardshipBond,
    StewardshipRegistry,
)
from .lifecycle_audit_logger import LifecycleAuditLogger, LifecycleEvent

__all__ = [
    "GAIANLifecycleState",
    "LifecycleTransitionError",
    "VALID_TRANSITIONS",
    "LifecycleManager",
    "StewardRole",
    "StewardshipBond",
    "StewardshipRegistry",
    "LifecycleAuditLogger",
    "LifecycleEvent",
]
