"""
core/lifecycle/__init__.py
C27 Phase 1 + Phase 2 (hardened) exports
"""

from .gaian_lifecycle_state import GAIANLifecycleState, LifecycleTransitionError, VALID_TRANSITIONS
from .lifecycle_manager import LifecycleManager
from .stewardship import StewardRole, StewardshipBond, StewardshipRegistry
from .lifecycle_audit_logger import LifecycleAuditLogger, LifecycleEvent
from .adoption_queue import AdoptionQueue, AdoptionQueueEntry, AdoptionVisibility
from .compliance_sentinel import ComplianceSentinel, SentinelFinding, SentinelSeverity, SentinelCheckID
from .permissions import PermissionManager, PermissionEnvelope, LifecycleRole
from .ed25519_audit import CanonicalAuditEntry, AuditSignature, Phase2Ed25519BridgeSigner
from .retirement_engine import RetirementEngine, RetirementReason, RetirementRecord, LegacyPackage
from .signing import GAIASecretVault, InProcessVault, VaultKeyNotFoundError, Ed25519LifecycleSigner

__all__ = [
    "GAIANLifecycleState", "LifecycleTransitionError", "VALID_TRANSITIONS",
    "LifecycleManager",
    "StewardRole", "StewardshipBond", "StewardshipRegistry",
    "LifecycleAuditLogger", "LifecycleEvent",
    "AdoptionQueue", "AdoptionQueueEntry", "AdoptionVisibility",
    "ComplianceSentinel", "SentinelFinding", "SentinelSeverity", "SentinelCheckID",
    "PermissionManager", "PermissionEnvelope", "LifecycleRole",
    "CanonicalAuditEntry", "AuditSignature", "Phase2Ed25519BridgeSigner",
    "RetirementEngine", "RetirementReason", "RetirementRecord", "LegacyPackage",
    "GAIASecretVault", "InProcessVault", "VaultKeyNotFoundError", "Ed25519LifecycleSigner",
]
