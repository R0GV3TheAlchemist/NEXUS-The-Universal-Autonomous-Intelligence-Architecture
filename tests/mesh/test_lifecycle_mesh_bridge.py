"""
tests/mesh/test_lifecycle_mesh_bridge.py
C26 / C27 — LifecycleMeshBridge integration tests
"""

from __future__ import annotations

import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from core.mesh.p2p_mesh import P2PMesh, PeerRecord
from core.mesh.node import GaiaNode
from core.mesh.lifecycle_mesh_bridge import (
    LifecycleEventEnvelope,
    LifecycleMeshBridge,
    LifecycleMeshAdapter,
    TOPIC_LIFECYCLE,
)
from core.lifecycle import (
    LifecycleManager,
    InProcessVault,
    Ed25519LifecycleSigner,
    GAIANLifecycleState,
)
from core.lifecycle.lifecycle_audit_logger import LifecycleEvent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_node(display_name: str = "test-node") -> GaiaNode:
    """Create an isolated GaiaNode with a temp identity directory."""
    tmp = tempfile.mkdtemp()
    node = GaiaNode.__new__(GaiaNode)
    node.IDENTITY_PATH = os.path.join(tmp, "identity.json")
    node.KEY_PATH      = os.path.join(tmp, "key.bin")
    node._private_key_bytes = None
    node._peers = {}
    node.identity = node._load_or_create(display_name, gaian_id=None)
    return node


def _make_event(
    gaian_id: str = "g-test",
    event_type: str = "ACTIVATE",
    from_state = GAIANLifecycleState.BORN,
    to_state   = GAIANLifecycleState.ACTIVE,
) -> LifecycleEvent:
    return LifecycleEvent(
        gaian_id=gaian_id,
        seq=1,
        event_type=event_type,
        from_state=from_state,
        to_state=to_state,
        actor_id="s-test",
        metadata={},
        logged_at="2026-07-14T00:00:00+00:00",
        hmac_sig="deadbeef",
    )


def _make_signer() -> Ed25519LifecycleSigner:
    vault = InProcessVault()
    vault.generate_key("k")
    return Ed25519LifecycleSigner(vault=vault, key_id="k")


# ---------------------------------------------------------------------------
# LifecycleEventEnvelope
# ---------------------------------------------------------------------------

class TestLifecycleEventEnvelope:

    def test_sign_and_verify(self):
        node = _make_node()
        env = LifecycleEventEnvelope(
            gaian_id="g1", event_type="ACTIVATE",
            from_state="BORN", to_state="ACTIVE",
        )
        env.sign(node)
        assert env.signature != ""
        assert env.verify_signature() is True

    def test_tampered_payload_fails_verify(self):
        node = _make_node()
        env = LifecycleEventEnvelope(gaian_id="g1", event_type="ACTIVATE")
        env.sign(node)
        env.gaian_id = "g-evil"   # tamper after signing
        assert env.verify_signature() is False

    def test_empty_signature_fails_verify(self):
        env = LifecycleEventEnvelope(gaian_id="g1", event_type="ACTIVATE")
        assert env.verify_signature() is False

    def test_round_trip_serialisation(self):
        node = _make_node()
        env = LifecycleEventEnvelope(
            gaian_id="g1", event_type="RETIRE",
            from_state="ACTIVE", to_state="RETIRED",
            metadata={"reason": "test"},
        )
        env.sign(node)
        restored = LifecycleEventEnvelope.from_dict(env.to_dict())
        assert restored.gaian_id     == "g1"
        assert restored.event_type   == "RETIRE"
        assert restored.signature    == env.signature
        assert restored.verify_signature() is True

    def test_from_lifecycle_event(self):
        node  = _make_node()
        event = _make_event()
        env   = LifecycleEventEnvelope.from_lifecycle_event(event, node)
        assert env.gaian_id   == "g-test"
        assert env.event_type == "ACTIVATE"
        assert env.to_state   == "ACTIVE"
        assert env.verify_signature() is True


# ---------------------------------------------------------------------------
# LifecycleMeshBridge — publish / receive
# ---------------------------------------------------------------------------

class TestLifecycleMeshBridge:

    def test_publish_calls_mesh_gossip(self):
        node  = _make_node()
        mesh  = P2PMesh(node_id=node.identity.node_id)
        bridge = LifecycleMeshBridge(node=node, mesh=mesh)
        event = _make_event()
        env   = bridge.publish(event)
        assert env is not None
        assert bridge.stats.published == 1

    def test_inbound_handler_receives_verified_event(self):
        node_a = _make_node("node-a")
        node_b = _make_node("node-b")
        mesh_a = P2PMesh(node_id=node_a.identity.node_id)
        mesh_b = P2PMesh(node_id=node_b.identity.node_id)

        bridge_a = LifecycleMeshBridge(node=node_a, mesh=mesh_a)
        bridge_b = LifecycleMeshBridge(node=node_b, mesh=mesh_b)

        received = []
        bridge_b.add_inbound_handler(received.append)

        # Simulate: envelope published on mesh_a → mesh_b receives it
        event = _make_event(gaian_id="g-sync")
        env   = LifecycleEventEnvelope.from_lifecycle_event(event, node_a)
        from core.mesh.p2p_mesh import GossipEnvelope
        gossip = GossipEnvelope(
            origin_node=node_a.identity.node_id,
            topic=TOPIC_LIFECYCLE,
            payload=env.to_dict(),
        )
        bridge_b._on_gossip_envelope(gossip)

        assert len(received) == 1
        assert received[0].gaian_id == "g-sync"
        assert bridge_b.stats.dispatched == 1

    def test_tampered_signature_dropped(self):
        node_a = _make_node("node-a")
        node_b = _make_node("node-b")
        mesh_b = P2PMesh(node_id=node_b.identity.node_id)
        bridge_b = LifecycleMeshBridge(node=node_b, mesh=mesh_b)

        received = []
        bridge_b.add_inbound_handler(received.append)

        event = _make_event()
        env   = LifecycleEventEnvelope.from_lifecycle_event(event, node_a)
        env.gaian_id = "g-tampered"  # tamper

        from core.mesh.p2p_mesh import GossipEnvelope
        gossip = GossipEnvelope(
            origin_node=node_a.identity.node_id,
            topic=TOPIC_LIFECYCLE,
            payload=env.to_dict(),
        )
        bridge_b._on_gossip_envelope(gossip)

        assert len(received) == 0
        assert bridge_b.stats.sig_failures == 1

    def test_loopback_own_origin_skipped(self):
        node  = _make_node()
        mesh  = P2PMesh(node_id=node.identity.node_id)
        bridge = LifecycleMeshBridge(node=node, mesh=mesh)

        received = []
        bridge.add_inbound_handler(received.append)

        event = _make_event()
        env   = LifecycleEventEnvelope.from_lifecycle_event(event, node)

        from core.mesh.p2p_mesh import GossipEnvelope
        gossip = GossipEnvelope(
            origin_node=node.identity.node_id,
            topic=TOPIC_LIFECYCLE,
            payload=env.to_dict(),
        )
        bridge._on_gossip_envelope(gossip)
        assert len(received) == 0
        assert bridge.stats.duplicates == 1

    def test_strict_mode_rejects_unknown_sender(self):
        node_a = _make_node("node-a")
        node_b = _make_node("node-b")
        mesh_b = P2PMesh(node_id=node_b.identity.node_id)
        bridge_b = LifecycleMeshBridge(node=node_b, mesh=mesh_b, strict_sender_check=True)
        # node_a is NOT registered as a known node

        received = []
        bridge_b.add_inbound_handler(received.append)

        event = _make_event()
        env   = LifecycleEventEnvelope.from_lifecycle_event(event, node_a)

        from core.mesh.p2p_mesh import GossipEnvelope
        gossip = GossipEnvelope(
            origin_node=node_a.identity.node_id,
            topic=TOPIC_LIFECYCLE,
            payload=env.to_dict(),
        )
        bridge_b._on_gossip_envelope(gossip)
        assert len(received) == 0
        assert bridge_b.stats.sig_failures == 1

    def test_strict_mode_accepts_registered_sender(self):
        node_a = _make_node("node-a")
        node_b = _make_node("node-b")
        mesh_b = P2PMesh(node_id=node_b.identity.node_id)
        bridge_b = LifecycleMeshBridge(node=node_b, mesh=mesh_b, strict_sender_check=True)
        bridge_b.register_known_node(
            node_a.identity.node_id,
            node_a.identity.public_key_bytes.hex(),
        )

        received = []
        bridge_b.add_inbound_handler(received.append)

        event = _make_event()
        env   = LifecycleEventEnvelope.from_lifecycle_event(event, node_a)

        from core.mesh.p2p_mesh import GossipEnvelope
        gossip = GossipEnvelope(
            origin_node=node_a.identity.node_id,
            topic=TOPIC_LIFECYCLE,
            payload=env.to_dict(),
        )
        bridge_b._on_gossip_envelope(gossip)
        assert len(received) == 1

    def test_handler_registration_and_removal(self):
        node   = _make_node()
        mesh   = P2PMesh(node_id=node.identity.node_id)
        bridge = LifecycleMeshBridge(node=node, mesh=mesh)

        calls = []
        handler = calls.append
        bridge.add_inbound_handler(handler)
        assert handler in bridge._inbound_handlers
        bridge.remove_inbound_handler(handler)
        assert handler not in bridge._inbound_handlers

    def test_no_mesh_publish_returns_none(self):
        node   = _make_node()
        bridge = LifecycleMeshBridge(node=node)  # no mesh
        event  = _make_event()
        result = bridge.publish(event)
        assert result is None
        assert bridge.stats.published == 0


# ---------------------------------------------------------------------------
# LifecycleMeshAdapter — end-to-end wiring
# ---------------------------------------------------------------------------

class TestLifecycleMeshAdapter:

    def test_adapter_publishes_on_genesis(self):
        node    = _make_node()
        mesh    = P2PMesh(node_id=node.identity.node_id)
        bridge  = LifecycleMeshBridge(node=node, mesh=mesh)
        mgr     = LifecycleManager(signer=_make_signer())
        adapter = LifecycleMeshAdapter(manager=mgr, bridge=bridge)

        mgr.register_latent("g-adapt")
        mgr.genesis("g-adapt", steward_id="s-adapt")
        assert bridge.stats.published >= 1

    def test_adapter_publishes_on_activate(self):
        node    = _make_node()
        mesh    = P2PMesh(node_id=node.identity.node_id)
        bridge  = LifecycleMeshBridge(node=node, mesh=mesh)
        mgr     = LifecycleManager(signer=_make_signer())
        adapter = LifecycleMeshAdapter(manager=mgr, bridge=bridge)

        mgr.register_latent("g-act")
        mgr.genesis("g-act", steward_id="s1")
        count_after_genesis = bridge.stats.published
        mgr.activate("g-act", actor_id="s1",
                     justification="ready", trigger_class="STEWARD_ACTION")
        assert bridge.stats.published > count_after_genesis

    def test_remote_event_callback(self):
        node_a  = _make_node("node-a")
        node_b  = _make_node("node-b")
        mesh_b  = P2PMesh(node_id=node_b.identity.node_id)
        bridge_b = LifecycleMeshBridge(node=node_b, mesh=mesh_b)
        mgr_b   = LifecycleManager(signer=_make_signer())
        adapter = LifecycleMeshAdapter(manager=mgr_b, bridge=bridge_b)

        remote_events = []
        adapter.on_remote_event = remote_events.append

        event = _make_event(gaian_id="g-remote")
        env   = LifecycleEventEnvelope.from_lifecycle_event(event, node_a)

        from core.mesh.p2p_mesh import GossipEnvelope
        gossip = GossipEnvelope(
            origin_node=node_a.identity.node_id,
            topic=TOPIC_LIFECYCLE,
            payload=env.to_dict(),
        )
        bridge_b._on_gossip_envelope(gossip)
        assert len(remote_events) == 1
        assert remote_events[0].gaian_id == "g-remote"
