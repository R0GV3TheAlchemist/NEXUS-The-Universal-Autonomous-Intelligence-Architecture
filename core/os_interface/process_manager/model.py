"""
GAIA Process Model — typed processes with capability sets and identity binding.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProcessKind(str, Enum):
    KERNEL = "kernel"              # kernel server process
    DRIVER = "driver"              # hardware driver (user-space, isolated)
    SYSTEM = "system"              # OS system service
    INTELLIGENCE = "intelligence"  # GAIA AI runtime — first-class kind
    APPLICATION = "application"    # user application
    SANDBOX = "sandbox"            # maximally isolated, no network, no FS
    GUEST = "guest"                # guest OS personality process


class ProcessIsolationLevel(str, Enum):
    KERNEL = "kernel"      # ring 0, full hardware access
    TRUSTED = "trusted"    # ring 1, system services
    USER = "user"          # ring 3, standard isolation
    STRICT = "strict"      # ring 3 + seccomp-like syscall filter
    SANDBOX = "sandbox"    # ring 3 + no ambient capabilities


@dataclass
class ProcessIdentity:
    """Cryptographic principal binding for a process."""
    owner_id: str = ""         # GAIA principal ID
    session_id: str = ""       # session this process belongs to
    space_id: str = ""         # space context
    signing_key_id: str = ""   # key used to sign this process image
    trusted: bool = False


class ResourceKind(str, Enum):
    MEMORY = "memory"
    FILE = "file"
    NETWORK = "network"
    IPC_PORT = "ipc_port"
    DEVICE = "device"
    CLOCK = "clock"
    GPU = "gpu"
    NEURAL_ENGINE = "neural_engine"
    DISPLAY = "display"
    AUDIO = "audio"


@dataclass
class CapabilityGrant:
    """An unforgeable, explicit grant of access to a named resource."""
    capability_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    resource_kind: ResourceKind = ResourceKind.MEMORY
    resource_id: str = ""
    read: bool = True
    write: bool = False
    execute: bool = False
    delegate: bool = False     # can this process re-grant this capability?
    revoked: bool = False
    granted_at: str = field(default_factory=_utcnow)
    granted_by: str = ""       # pid of granting process
    expires_at: Optional[str] = None

    def is_active(self) -> bool:
        return not self.revoked


@dataclass
class CapabilitySet:
    """The complete set of capabilities held by a process."""
    grants: List[CapabilityGrant] = field(default_factory=list)

    def add(self, grant: CapabilityGrant) -> None:
        self.grants.append(grant)

    def revoke(self, capability_id: str) -> bool:
        for g in self.grants:
            if g.capability_id == capability_id:
                g.revoked = True
                return True
        return False

    def active(self) -> List[CapabilityGrant]:
        return [g for g in self.grants if g.is_active()]

    def has(self, resource_kind: ResourceKind, resource_id: str = "") -> bool:
        for g in self.active():
            if g.resource_kind == resource_kind:
                if not resource_id or g.resource_id == resource_id:
                    return True
        return False

    def for_resource(self, resource_id: str) -> List[CapabilityGrant]:
        return [g for g in self.active() if g.resource_id == resource_id]


@dataclass
class GAIAProcess:
    """A fully isolated, capability-governed execution unit."""
    name: str
    pid: str = field(default_factory=lambda: str(uuid.uuid4()))
    kind: ProcessKind = ProcessKind.APPLICATION
    isolation: ProcessIsolationLevel = ProcessIsolationLevel.USER
    identity: ProcessIdentity = field(default_factory=ProcessIdentity)
    capabilities: CapabilitySet = field(default_factory=CapabilitySet)
    parent_pid: Optional[str] = None
    children: List[str] = field(default_factory=list)   # child pids
    ipc_ports: List[str] = field(default_factory=list)  # port ids
    exit_code: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utcnow)
    started_at: Optional[str] = None
    exited_at: Optional[str] = None

    def is_intelligence(self) -> bool:
        return self.kind == ProcessKind.INTELLIGENCE

    def is_alive(self) -> bool:
        return self.exit_code is None

    def grant(self, grant: CapabilityGrant) -> None:
        self.capabilities.add(grant)

    def summary(self) -> Dict[str, Any]:
        return {
            "pid": self.pid,
            "name": self.name,
            "kind": self.kind.value,
            "isolation": self.isolation.value,
            "owner_id": self.identity.owner_id,
            "alive": self.is_alive(),
            "capabilities": len(self.capabilities.active()),
            "children": list(self.children),
            "ipc_ports": list(self.ipc_ports),
        }
