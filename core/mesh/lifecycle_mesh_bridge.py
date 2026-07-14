"""
core/mesh/lifecycle_mesh_bridge.py
C26 / C27 — Lifecycle Event Mesh Synchronisation

Propagates C27 GAIAN lifecycle state transitions and stewardship
events across the C26 P2P mesh so every node in the GAIA network
maintains a coherent view of each GAIAN's current lifecycle state.

Architecture
------------

    LifecycleManager  (C27)
         │  emits events
         ▼
    LifecycleMeshAdapter        ← attach() to wire up
         │  wraps / publishes
         ▼
    LifecycleMeshBridge         ← owns mesh subscription
         │  calls mesh.gossip()
         ▼
    P2PMesh (C26)               ← topic: "lifecycle.event"
         │  receives + routes
         ▼
    LifecycleMeshBridge.on_inbound()
         │  verify Ed25519 sig
         ▼
    registered inbound handlers  ← local reaction / persistence

Topics
------
  lifecycle.event   — state transitions, stewardship bonds, retirements
  lifecycle.query   — (future) pull-based state reconciliation

Security
--------
Every outbound LifecycleEventEnvelope is signed by the originating
node using its GaiaNode Ed25519 key (from core/mesh/node.py).
Inbound envelopes are verified against the sender's public key.
Envelopes that fail signature verification are silently dropped and
counted in `bridge.stats.sig_failures`.

Canon-refs: C26, C27, C04, C47
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from core.mesh.p2p_mesh import GossipEnvelope, P2PMesh
from core.mesh.node import GaiaNode
from core.lifecycle.lifecycle_audit_logger import LifecycleEvent
from core.lifecycle.gaian_lifecycle_state import GAIANLifecycleState

logger = logging.getLogger("gaia.mesh.lifecycle")


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TOPIC_LIFECYCLE  = "lifecycle.event"
TOPIC_QUERY      = "lifecycle.query"
SCHEMA_VERSION   = "1.0"


# ---------------------------------------------------------------------------
# LifecycleEventEnvelope
# ---------------------------------------------------------------------------

@dataclass
class LifecycleEventEnvelope:
    """
    A signed, versioned lifecycle event payload for mesh propagation.

    Fields
    ------
    envelope_id     : Unique ID (UUID4) — used for gossip dedup.
    schema_version  : Schema version string for forward compatibility.
    origin_node_id  : node_id of the node that originated this event.
    origin_pub_key  : Hex-encoded Ed25519 public key of origin node.
    gaian_id        : The GAIAN this event concerns.
    event_type      : C27 event type string (e.g. "ACTIVATE").
    from_state      : Previous lifecycle state value (or None).
    to_state        : New lifecycle state value (or None).
    actor_id        : Steward / system actor that triggered the event.
    audit_entry_hash: SHA-256 of the CanonicalAuditEntry JSON (integrity tie).
    timestamp       : Unix timestamp (float) at time of origination.
    metadata        : Arbitrary extra data (e.g. steward role, reason).
    signature       : Hex-encoded Ed25519 signature over canonical payload.
    """

    envelope_id:       str   = field(default_factory=lambda: str(uuid.uuid4()))
    schema_version:    str   = SCHEMA_VERSION
    origin_node_id:    str   = ""
    origin_pub_key:    str   = ""   # hex
    gaian_id:          str   = ""
    event_type:        str   = ""
    from_state:        Optional[str] = None
    to_state:          Optional[str] = None
    actor_id:          Optional[str] = None
    audit_entry_hash:  Optional[str] = None   # SHA-256 hex
    timestamp:         float = field(default_factory=time.time)
    metadata:          dict  = field(default_factory=dict)
    signature:         str   = ""   # hex Ed25519

    # ------------------------------------------------------------------
    # Canonical payload (signed bytes — excludes signature field)
    # ------------------------------------------------------------------

    def _canonical_bytes(self) -> bytes:
        """Deterministic UTF-8 JSON of all fields except signature."""
        d = {
            "envelope_id":      self.envelope_id,
            "schema_version":   self.schema_version,
            "origin_node_id":   self.origin_node_id,
            "origin_pub_key":   self.origin_pub_key,
            "gaian_id":         self.gaian_id,
            "event_type":       self.event_type,
            "from_state":       self.from_state,
            "to_state":         self.to_state,
            "actor_id":         self.actor_id,
            "audit_entry_hash": self.audit_entry_hash,
            "timestamp":        self.timestamp,
            "metadata":         self.metadata,
        }
        return json.dumps(d, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def sign(self, node: GaiaNode) -> None:
        """Sign the canonical payload using *node*'s Ed25519 private key."""
        self.origin_node_id  = node.identity.node_id
        self.origin_pub_key  = node.identity.public_key_bytes.hex()
        self.signature       = node.sign(self._canonical_bytes()).hex()

    def verify_signature(self) -> bool:
        """Verify the envelope's Ed25519 signature. Returns False on failure."""
        if not self.signature or not self.origin_pub_key:
            return False
        try:
            pub_bytes = bytes.fromhex(self.origin_pub_key)
            sig_bytes = bytes.fromhex(self.signature)
        except ValueError:
            return False
        return GaiaNode.verify(pub_bytes, self._canonical_bytes(), sig_bytes)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "envelope_id":      self.envelope_id,
            "schema_version":   self.schema_version,
            "origin_node_id":   self.origin_node_id,
            "origin_pub_key":   self.origin_pub_key,
            "gaian_id":         self.gaian_id,
            "event_type":       self.event_type,
            "from_state":       self.from_state,
            "to_state":         self.to_state,
            "actor_id":         self.actor_id,
            "audit_entry_hash": self.audit_entry_hash,
            "timestamp":        self.timestamp,
            "metadata":         self.metadata,
            "signature":        self.signature,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "LifecycleEventEnvelope":
        return cls(
            envelope_id=d.get("envelope_id", str(uuid.uuid4())),
            schema_version=d.get("schema_version", SCHEMA_VERSION),
            origin_node_id=d.get("origin_node_id", ""),
            origin_pub_key=d.get("origin_pub_key", ""),
            gaian_id=d.get("gaian_id", ""),
            event_type=d.get("event_type", ""),
            from_state=d.get("from_state"),
            to_state=d.get("to_state"),
            actor_id=d.get("actor_id"),
            audit_entry_hash=d.get("audit_entry_hash"),
            timestamp=d.get("timestamp", time.time()),
            metadata=d.get("metadata", {}),
            signature=d.get("signature", ""),
        )

    @classmethod
    def from_lifecycle_event(
        cls,
        event:            LifecycleEvent,
        node:             GaiaNode,
        audit_entry_hash: Optional[str] = None,
        metadata:         Optional[dict] = None,
    ) -> "LifecycleEventEnvelope":
        """
        Construct and sign a LifecycleEventEnvelope from a LifecycleEvent.
        """
        env = cls(
            gaian_id=event.gaian_id,
            event_type=event.event_type,
            from_state=event.from_state.value if event.from_state else None,
            to_state=event.to_state.value   if event.to_state   else None,
            actor_id=event.actor_id,
            audit_entry_hash=audit_entry_hash,
            metadata=metadata or event.metadata or {},
        )
        env.sign(node)
        return env


# ---------------------------------------------------------------------------
# BridgeStats
# ---------------------------------------------------------------------------

@dataclass
class BridgeStats:
    """Running counters for the lifecycle mesh bridge."""
    published:    int = 0
    received:     int = 0
    dispatched:   int = 0
    sig_failures: int = 0
    duplicates:   int = 0


# ---------------------------------------------------------------------------
# InboundHandler type alias
# ---------------------------------------------------------------------------

InboundHandler = Callable[[LifecycleEventEnvelope], None]


# ---------------------------------------------------------------------------
# LifecycleMeshBridge
# ---------------------------------------------------------------------------

class LifecycleMeshBridge:
    """
    Bidirectional bridge between the C27 lifecycle system and the C26 mesh.

    Outbound
    --------
    Call ``publish(event, audit_entry_hash)`` to gossip a lifecycle
    event to all mesh peers.

    Inbound
    -------
    Subscribe the bridge to the P2PMesh via ``attach_to_mesh(mesh)``.
    Register handlers with ``add_inbound_handler(fn)``.
    All handlers are called with a verified LifecycleEventEnvelope.

    Strict mode
    -----------
    When ``strict_sender_check=True`` (default False), inbound envelopes
    from node IDs not present in ``known_nodes`` are rejected. In
    permissive mode only signature validation is enforced.
    """

    def __init__(
        self,
        node:                GaiaNode,
        mesh:                Optional[P2PMesh] = None,
        strict_sender_check: bool = False,
    ) -> None:
        self._node               = node
        self._mesh:  Optional[P2PMesh] = None
        self._strict             = strict_sender_check
        self._known_nodes:       Dict[str, str] = {}  # node_id → pub_key hex
        self._inbound_handlers:  List[InboundHandler] = []
        self.stats               = BridgeStats()

        if mesh is not None:
            self.attach_to_mesh(mesh)

    # ------------------------------------------------------------------
    # Mesh attachment
    # ------------------------------------------------------------------

    def attach_to_mesh(self, mesh: P2PMesh) -> None:
        """Subscribe to the lifecycle topic on *mesh*."""
        self._mesh = mesh
        mesh.subscribe(TOPIC_LIFECYCLE, self._on_gossip_envelope)
        logger.info(
            "[LifecycleMeshBridge] Attached to mesh node %s on topic '%s'",
            mesh.node_id, TOPIC_LIFECYCLE,
        )

    def detach_from_mesh(self) -> None:
        """Unsubscribe from the mesh topic."""
        if self._mesh is not None:
            self._mesh.unsubscribe(TOPIC_LIFECYCLE, self._on_gossip_envelope)
            self._mesh = None

    # ------------------------------------------------------------------
    # Known-node registry (for strict sender checks)
    # ------------------------------------------------------------------

    def register_known_node(self, node_id: str, pub_key_hex: str) -> None:
        """Pre-register a trusted node public key for strict mode."""
        self._known_nodes[node_id] = pub_key_hex

    # ------------------------------------------------------------------
    # Outbound: publish a lifecycle event to the mesh
    # ------------------------------------------------------------------

    def publish(
        self,
        event:            LifecycleEvent,
        audit_entry_hash: Optional[str] = None,
        metadata:         Optional[dict] = None,
    ) -> Optional[LifecycleEventEnvelope]:
        """
        Construct, sign, and gossip a LifecycleEventEnvelope.
        Returns the envelope, or None if no mesh is attached.
        """
        if self._mesh is None:
            logger.debug("[LifecycleMeshBridge] No mesh attached — event not published.")
            return None

        env = LifecycleEventEnvelope.from_lifecycle_event(
            event=event,
            node=self._node,
            audit_entry_hash=audit_entry_hash,
            metadata=metadata,
        )
        self._mesh.gossip(TOPIC_LIFECYCLE, env.to_dict())
        self.stats.published += 1
        logger.info(
            "[LifecycleMeshBridge] Published %s for GAIAN %s → %s",
            env.event_type, env.gaian_id, env.to_state,
        )
        return env

    # ------------------------------------------------------------------
    # Inbound: receive from P2PMesh subscription
    # ------------------------------------------------------------------

    def _on_gossip_envelope(self, gossip: GossipEnvelope) -> None:
        """Called by P2PMesh when a 'lifecycle.event' message arrives."""
        self.stats.received += 1
        try:
            env = LifecycleEventEnvelope.from_dict(gossip.payload)
        except Exception as exc:
            logger.warning("[LifecycleMeshBridge] Malformed envelope: %s", exc)
            return

        # Skip own-origin re-deliveries (gossip loopback)
        if env.origin_node_id == self._node.identity.node_id:
            self.stats.duplicates += 1
            return

        # Strict sender check
        if self._strict:
            known_key = self._known_nodes.get(env.origin_node_id)
            if known_key is None:
                logger.warning(
                    "[LifecycleMeshBridge] Unknown sender %s — rejected (strict mode).",
                    env.origin_node_id,
                )
                self.stats.sig_failures += 1
                return

        # Ed25519 signature verification
        if not env.verify_signature():
            logger.warning(
                "[LifecycleMeshBridge] Signature verification FAILED for envelope %s "
                "from node %s — dropping.",
                env.envelope_id, env.origin_node_id,
            )
            self.stats.sig_failures += 1
            return

        # Dispatch to registered handlers
        self.stats.dispatched += 1
        for handler in list(self._inbound_handlers):
            try:
                handler(env)
            except Exception as exc:
                logger.warning("[LifecycleMeshBridge] Inbound handler error: %s", exc)

    # ------------------------------------------------------------------
    # Handler registration
    # ------------------------------------------------------------------

    def add_inbound_handler(self, handler: InboundHandler) -> None:
        """Register a handler called for every verified inbound event."""
        if handler not in self._inbound_handlers:
            self._inbound_handlers.append(handler)

    def remove_inbound_handler(self, handler: InboundHandler) -> None:
        """Unregister an inbound handler."""
        try:
            self._inbound_handlers.remove(handler)
        except ValueError:
            pass


# ---------------------------------------------------------------------------
# LifecycleMeshAdapter
# ---------------------------------------------------------------------------

class LifecycleMeshAdapter:
    """
    Attaches a LifecycleMeshBridge to a LifecycleManager so that
    every lifecycle event is automatically published to the mesh.

    Usage::

        from core.mesh.lifecycle_mesh_bridge import LifecycleMeshAdapter
        from core.mesh.p2p_mesh import get_p2p_mesh
        from core.mesh.node import GaiaNode

        node    = GaiaNode(display_name="my-node")
        mesh    = get_p2p_mesh()
        bridge  = LifecycleMeshBridge(node=node, mesh=mesh)
        adapter = LifecycleMeshAdapter(manager=mgr, bridge=bridge)

        # Optional: react to remote events
        adapter.on_remote_event = lambda env: print(env.event_type)

    The adapter intercepts lifecycle events by wrapping
    LifecycleManager._post_event() (if it exists) or by registering
    a post-commit hook via manager.add_event_hook() (preferred when
    LifecycleManager exposes it). Falls back to a lightweight
    monkey-patch of manager._emit_event for maximum compatibility.
    """

    def __init__(
        self,
        manager,   # LifecycleManager — avoid circular import by not typing
        bridge: LifecycleMeshBridge,
    ) -> None:
        self._manager = manager
        self._bridge  = bridge
        self.on_remote_event: Optional[Callable[[LifecycleEventEnvelope], None]] = None

        # Register inbound handler so remote events flow back to caller
        self._bridge.add_inbound_handler(self._handle_remote)

        # Wire outbound: patch manager's _emit_event if present,
        # otherwise wrap the audit logger's append method.
        self._wire_outbound()

    def _wire_outbound(self) -> None:
        """
        Intercept lifecycle events as they are emitted by LifecycleManager.
        Strategy: wrap manager._audit_logger.append (the common hook point)
        so every appended LifecycleEvent is also published to the mesh.
        The original append is always called first (WAL integrity preserved).
        """
        logger_obj = getattr(self._manager, "_audit_logger", None)
        if logger_obj is None:
            logger.warning("[LifecycleMeshAdapter] No _audit_logger on manager — outbound disabled.")
            return

        original_append = logger_obj.append

        bridge = self._bridge

        def _wrapped_append(event: LifecycleEvent) -> None:
            original_append(event)          # WAL: write to audit log first
            bridge.publish(event)           # then gossip to mesh

        logger_obj.append = _wrapped_append
        logger.info("[LifecycleMeshAdapter] Outbound hook wired via audit_logger.append.")

    def _handle_remote(self, env: LifecycleEventEnvelope) -> None:
        """Called for every verified inbound remote lifecycle event."""
        logger.info(
            "[LifecycleMeshAdapter] Remote event: GAIAN %s %s → %s (from node %s)",
            env.gaian_id, env.from_state, env.to_state, env.origin_node_id,
        )
        if self.on_remote_event is not None:
            self.on_remote_event(env)

    def detach(self) -> None:
        """Remove bridge inbound handler. Does not un-patch the audit logger."""
        self._bridge.remove_inbound_handler(self._handle_remote)
