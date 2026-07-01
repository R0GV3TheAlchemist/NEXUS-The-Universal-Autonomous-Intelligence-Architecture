"""
GAIA Network
The top-level coordinator for a multi-node GAIA deployment.
Orchestrates: nodes, sync, consensus, conflict resolution, global state.

Usage (simulation mode — no network required):

    net = GAIANetwork()
    node_a = net.add_node("node-a", domain="biophotonics", trust=0.9)
    node_b = net.add_node("node-b", domain="architecture", trust=0.85)

    # Each node ingests claims independently
    node_a.update_state(claim_id, entry)
    node_b.update_state(claim_id, entry)

    # Sync + consensus
    result = net.sync_and_resolve()
    print(result["consensus"])
    print(result["agreement"])
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .node import GAIANode
from .global_state import GlobalWorldState
from .consensus import ConsensusEngine
from .conflict import ConflictResolver


class GAIANetwork:
    """
    Top-level coordinator for a distributed GAIA deployment.
    In v0.4: simulation mode (in-process, no HTTP).
    In v0.5+: live multi-process / multi-machine deployment.
    """

    def __init__(self, mode: str = "simulation"):
        self.mode = mode
        self._nodes: Dict[str, GAIANode] = {}
        self.global_state  = GlobalWorldState()
        self.consensus     = ConsensusEngine()
        self.conflict      = ConflictResolver()
        self._sync_history: List[Dict] = []
        self._created_at   = datetime.utcnow()
        print(f"  GAIANetwork initialised (mode={mode}) at {self._created_at.isoformat()}")

    def add_node(
        self,
        name: str,
        domain: Optional[str] = None,
        trust: float = 1.0
    ) -> GAIANode:
        """Register a new node in the network."""
        node = GAIANode(
            name=name,
            domain_specialisation=domain,
            trust_score=trust
        )
        self._nodes[node.id] = node
        print(f"  + Node registered: {node}")
        return node

    def get_node(self, node_id: str) -> Optional[GAIANode]:
        return self._nodes.get(node_id)

    def sync_and_resolve(self) -> Dict[str, Any]:
        """
        Full six-step distributed sync cycle:
        1. Collect all node state snapshots
        2. Push to global state
        3. Merge all perspectives
        4. Detect conflicts
        5. Form consensus
        6. Compute agreement level
        Returns full sync result.
        """
        # Step 1+2: Collect node states
        for node in self._nodes.values():
            snap = node.get_state_snapshot()
            self.global_state.update_node_state(node.id, snap)
            node.record_sync()

        # Step 3: Merge
        merged = self.global_state.merge_states()

        # Step 4: Detect conflicts
        conflicts = self.conflict.detect(
            {nid: snap for nid, snap in
             [(n.id, n.get_state_snapshot()) for n in self._nodes.values()]}
        )

        # Step 5: Consensus
        consensus = self.consensus.resolve(merged, self.global_state)

        # Step 6: Agreement
        agreement = self.consensus.agreement_level(merged)

        result = {
            "sync_timestamp":   datetime.utcnow().isoformat(),
            "nodes_synced":     len(self._nodes),
            "claims_merged":    len(merged),
            "conflicts":        conflicts,
            "consensus":        consensus,
            "agreement":        agreement,
            "global_stats":     self.global_state.stats()
        }
        self._sync_history.append(result)
        return result

    def network_stats(self) -> Dict[str, Any]:
        return {
            "mode":           self.mode,
            "total_nodes":    len(self._nodes),
            "total_syncs":    len(self._sync_history),
            "nodes":          [str(n) for n in self._nodes.values()],
            "global_state":   self.global_state.stats()
        }

    def __repr__(self) -> str:
        return (
            f"GAIANetwork(nodes={len(self._nodes)}, "
            f"syncs={len(self._sync_history)}, "
            f"mode={self.mode})"
        )
