"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NEXUS — The Universal Autonomous Intelligence Architecture
  Author   : Kyle Steen
  GitHub   : R0GV3TheAlchemist
  Email    : xxkylesteenxx@outlook.com
  License  : All Rights Reserved © 2026 Kyle Steen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

federation.py — NEXUS Federation Layer.

FederationNode capability manifests and health beacons,
FederationRegistry membership management, and pluggable
ConsensusProtocol (PBFT stub by default).
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
import time


class NodeState(Enum):
    OFFLINE  = auto()
    JOINING  = auto()
    ACTIVE   = auto()
    DEGRADED = auto()
    LEAVING  = auto()


@dataclass
class NodeCapabilityManifest:
    """Describes what a FederationNode can provide to the cluster."""
    node_id:             UUID           = field(default_factory=uuid4)
    capabilities:        List[str]      = field(default_factory=list)
    region:              str            = ""
    jurisdiction:        str            = ""
    max_throughput_gbps: float          = 0.0
    pqc_enabled:         bool           = False
    metadata:            Dict[str, Any] = field(default_factory=dict)


@dataclass
class HealthBeacon:
    """Periodic health signal broadcast by a FederationNode."""
    beacon_id:  UUID      = field(default_factory=uuid4)
    node_id:    UUID      = field(default_factory=uuid4)
    state:      NodeState = NodeState.ACTIVE
    cpu_pct:    float     = 0.0
    mem_pct:    float     = 0.0
    latency_ms: float     = 0.0
    timestamp:  float     = field(default_factory=time.time)


class FederationNode:
    """
    A sovereign NEXUS node participating in the federation cluster.
    Publishes a capability manifest and periodic health beacons.
    """

    def __init__(self, manifest: NodeCapabilityManifest) -> None:
        self.manifest  = manifest
        self.node_id   = manifest.node_id
        self._state    = NodeState.OFFLINE
        self._beacons: List[HealthBeacon] = []

    def join(self)     -> None: self._state = NodeState.JOINING
    def activate(self) -> None: self._state = NodeState.ACTIVE
    def degrade(self)  -> None: self._state = NodeState.DEGRADED
    def leave(self)    -> None: self._state = NodeState.LEAVING

    def beacon(self, cpu_pct: float = 0.0,
               mem_pct: float = 0.0,
               latency_ms: float = 0.0) -> HealthBeacon:
        hb = HealthBeacon(
            node_id=self.node_id, state=self._state,
            cpu_pct=cpu_pct, mem_pct=mem_pct, latency_ms=latency_ms,
        )
        self._beacons.append(hb)
        return hb

    @property
    def state(self) -> NodeState:
        return self._state

    def last_beacon(self) -> Optional[HealthBeacon]:
        return self._beacons[-1] if self._beacons else None


class ConsensusProtocol(ABC):
    """Abstract base for pluggable BFT consensus protocols."""

    @abstractmethod
    def propose(self, value: Any, node_id: UUID) -> bool: ...

    @abstractmethod
    def commit(self, value: Any) -> bool: ...


class PBFTConsensusStub(ConsensusProtocol):
    """
    Stub PBFT implementation.
    Replace with full PBFT or Tendermint integration in production.
    """

    def __init__(self, fault_tolerance: int = 1) -> None:
        self.fault_tolerance = fault_tolerance
        self._log: List[Dict[str, Any]] = []

    def propose(self, value: Any, node_id: UUID) -> bool:
        self._log.append({"phase": "PROPOSE", "value": str(value),
                          "node_id": str(node_id), "timestamp": time.time()})
        return True

    def commit(self, value: Any) -> bool:
        self._log.append({"phase": "COMMIT", "value": str(value),
                          "timestamp": time.time()})
        return True

    def log(self) -> List[Dict[str, Any]]:
        return list(self._log)


class FederationRegistry:
    """
    Maintains the live membership list of all FederationNodes.
    Routes cross-node requests to nodes by capability.
    """

    def __init__(self,
                 consensus: Optional[ConsensusProtocol] = None) -> None:
        self._nodes:     Dict[UUID, FederationNode] = {}
        self._consensus = consensus or PBFTConsensusStub()

    def register(self, node: FederationNode) -> None:
        node.join()
        self._nodes[node.node_id] = node

    def activate(self, node_id: UUID) -> None:
        node = self._nodes.get(node_id)
        if node:
            node.activate()

    def deregister(self, node_id: UUID) -> None:
        node = self._nodes.get(node_id)
        if node:
            node.leave()
            self._nodes.pop(node_id)

    def route(self, capability: str) -> List[FederationNode]:
        """Return all ACTIVE nodes advertising the requested capability."""
        return [
            n for n in self._nodes.values()
            if n.state == NodeState.ACTIVE
            and capability in n.manifest.capabilities
        ]

    def active_nodes(self) -> List[FederationNode]:
        return [n for n in self._nodes.values() if n.state == NodeState.ACTIVE]

    def all_nodes(self) -> List[FederationNode]:
        return list(self._nodes.values())

    def cluster_health(self) -> Dict[str, Any]:
        nodes   = self.all_nodes()
        beacons = [n.last_beacon() for n in nodes if n.last_beacon()]
        avg = lambda vals: sum(vals) / len(vals) if vals else 0.0
        return {
            "total_nodes":    len(nodes),
            "active_nodes":   len(self.active_nodes()),
            "avg_cpu_pct":    avg([b.cpu_pct    for b in beacons]),
            "avg_mem_pct":    avg([b.mem_pct    for b in beacons]),
            "avg_latency_ms": avg([b.latency_ms for b in beacons]),
        }
