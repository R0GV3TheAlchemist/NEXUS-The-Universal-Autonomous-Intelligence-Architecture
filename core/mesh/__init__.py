"""
core/mesh/__init__.py
C26 GAIA Mesh Layer
"""

from .p2p_mesh import P2PMesh, GossipEnvelope, PeerRecord, get_p2p_mesh
from .node import GaiaNode, NodeIdentity
from .lifecycle_mesh_bridge import (
    LifecycleMeshBridge,
    LifecycleMeshAdapter,
    LifecycleEventEnvelope,
    TOPIC_LIFECYCLE,
    TOPIC_QUERY,
)

__all__ = [
    # P2P mesh
    "P2PMesh", "GossipEnvelope", "PeerRecord", "get_p2p_mesh",
    # Node identity
    "GaiaNode", "NodeIdentity",
    # Lifecycle mesh sync (C26/C27)
    "LifecycleMeshBridge", "LifecycleMeshAdapter", "LifecycleEventEnvelope",
    "TOPIC_LIFECYCLE", "TOPIC_QUERY",
]
