"""IdentityVault — cryptographic identity, DID, and Nostr anchoring for GAIA-OS.

Architecture
------------
Each GAIAN session anchors to an Ed25519 keypair. The keypair drives:
  1. A W3C DID (did:key) — portable, self-sovereign identity.
  2. A Nostr npub/nsec pair — P2P broadcast anchor for MotherThread.
  3. A ZKP selective-disclosure credential scaffold — allows proving
     ownership of an attribute without revealing the raw value.

ZKP design (Scaffold)
---------------------
Full ZKP (zk-SNARKs / BLS12-381) requires a circuit library not yet
bundled with GAIA-OS. The scaffold here implements the commitment scheme
(Pedersen-style SHA-256 commitment) and the proof shape — the verify()
method is ready to be wired to an external prover.

Canon refs: C01 (Sovereignty), C58 (Aether / Noosphere P2P)
Issue: #260
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import (
        Encoding, PublicFormat, PrivateFormat, NoEncryption,
    )
    _CRYPTO_AVAILABLE = True
except ImportError:  # pragma: no cover
    _CRYPTO_AVAILABLE = False


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class KeyPair:
    """Ed25519 key pair representation."""
    private_key_bytes: bytes
    public_key_bytes: bytes

    @property
    def public_key_b64(self) -> str:
        return base64.urlsafe_b64encode(self.public_key_bytes).rstrip(b'=').decode()

    @property
    def private_key_b64(self) -> str:
        return base64.urlsafe_b64encode(self.private_key_bytes).rstrip(b'=').decode()


@dataclass
class DIDDocument:
    """Minimal W3C DID Document (did:key method)."""
    did: str
    public_key_b64: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            '@context': 'https://www.w3.org/ns/did/v1',
            'id': self.did,
            'verificationMethod': [{
                'id': f"{self.did}#key-1",
                'type': 'Ed25519VerificationKey2020',
                'controller': self.did,
                'publicKeyMultibase': 'z' + self.public_key_b64,
            }],
            'authentication': [f"{self.did}#key-1"],
            'created': self.created_at.isoformat(),
        }


@dataclass
class NostrIdentity:
    """Nostr identity anchored to an Ed25519 public key."""
    npub: str    # Bech32-like encoding (simplified — full bech32 needs separate lib)
    pubkey_hex: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class SelectiveDisclosureProof:
    """ZKP selective-disclosure commitment (Pedersen-style SHA-256 scaffold).

    Commitment scheme: C = SHA256(attribute || nonce)
    The prover reveals (attribute, nonce); the verifier recomputes C.
    This is the hash-commitment scaffold; a full ZK circuit replaces
    the verify() body when a prover library is available.
    """
    attribute_name: str
    commitment: str       # hex(SHA256(value || nonce))
    nonce_b64: str        # base64url-encoded 32-byte random nonce
    revealed_value: str | None = None  # Set only when owner chooses to reveal

    def verify(self, claimed_value: str) -> bool:
        """Verify that `claimed_value` matches the commitment.

        Returns True if SHA256(claimed_value || nonce) == commitment.
        """
        nonce = base64.urlsafe_b64decode(self.nonce_b64 + '==')
        h = hashlib.sha256(claimed_value.encode() + nonce).hexdigest()
        return hmac.compare_digest(h, self.commitment)


# ---------------------------------------------------------------------------
# Vault
# ---------------------------------------------------------------------------

class IdentityVault:
    """Cryptographic identity vault for a GAIAN session.

    Generates and holds:
    - Ed25519 KeyPair
    - W3C DID Document (did:key)
    - Nostr identity
    - Selective-disclosure commitments for sovereign attributes

    Usage
    -----
    vault = IdentityVault.generate(session_id='my-session')
    vault.commit_attribute('name', 'R0GV3')
    proof = vault.disclosure_proof('name')
    assert proof.verify('R0GV3')  # True
    """

    def __init__(self, session_id: str, keypair: KeyPair) -> None:
        self.session_id = session_id
        self.keypair = keypair
        self._disclosures: dict[str, SelectiveDisclosureProof] = {}
        self._did_document: DIDDocument | None = None
        self._nostr_identity: NostrIdentity | None = None

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def generate(cls, session_id: str) -> 'IdentityVault':
        """Generate a fresh Ed25519 keypair and return a new vault."""
        if _CRYPTO_AVAILABLE:
            private = Ed25519PrivateKey.generate()
            priv_bytes = private.private_bytes(
                Encoding.Raw, PrivateFormat.Raw, NoEncryption()
            )
            pub_bytes = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        else:
            # Fallback: deterministic from session_id (test / no-crypto env)
            priv_bytes = hashlib.sha256(session_id.encode()).digest()
            pub_bytes = hashlib.sha256(priv_bytes).digest()

        return cls(session_id=session_id, keypair=KeyPair(priv_bytes, pub_bytes))

    # ------------------------------------------------------------------
    # DID
    # ------------------------------------------------------------------

    def did_document(self) -> DIDDocument:
        """Return (or generate) the W3C DID Document for this vault."""
        if self._did_document is None:
            did = f"did:key:z{self.keypair.public_key_b64}"
            self._did_document = DIDDocument(
                did=did,
                public_key_b64=self.keypair.public_key_b64,
            )
        return self._did_document

    # ------------------------------------------------------------------
    # Nostr
    # ------------------------------------------------------------------

    def nostr_identity(self) -> NostrIdentity:
        """Return (or generate) a Nostr identity anchored to this vault."""
        if self._nostr_identity is None:
            pubkey_hex = self.keypair.public_key_bytes.hex()
            npub = 'npub1' + base64.urlsafe_b64encode(
                self.keypair.public_key_bytes
            ).rstrip(b'=').decode()[:32]
            self._nostr_identity = NostrIdentity(
                npub=npub,
                pubkey_hex=pubkey_hex,
            )
        return self._nostr_identity

    # ------------------------------------------------------------------
    # ZKP selective disclosure
    # ------------------------------------------------------------------

    def commit_attribute(self, attribute_name: str, value: str) -> SelectiveDisclosureProof:
        """Create a Pedersen-style SHA-256 commitment for `attribute_name`."""
        nonce = secrets.token_bytes(32)
        nonce_b64 = base64.urlsafe_b64encode(nonce).rstrip(b'=').decode()
        commitment = hashlib.sha256(value.encode() + nonce).hexdigest()
        proof = SelectiveDisclosureProof(
            attribute_name=attribute_name,
            commitment=commitment,
            nonce_b64=nonce_b64,
        )
        self._disclosures[attribute_name] = proof
        return proof

    def disclosure_proof(self, attribute_name: str) -> SelectiveDisclosureProof | None:
        """Return the disclosure proof for `attribute_name`, or None."""
        return self._disclosures.get(attribute_name)

    def list_committed_attributes(self) -> list[str]:
        """Return names of all committed attributes (no values exposed)."""
        return list(self._disclosures.keys())

    # ------------------------------------------------------------------
    # Signing
    # ------------------------------------------------------------------

    def sign(self, message: bytes) -> bytes:
        """Sign `message` with the vault’s Ed25519 private key."""
        if _CRYPTO_AVAILABLE:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
            priv = Ed25519PrivateKey.from_private_bytes(self.keypair.private_key_bytes)
            return priv.sign(message)
        # Fallback: HMAC-SHA256 (not Ed25519 — test env only)
        return hmac.new(self.keypair.private_key_bytes, message, hashlib.sha256).digest()

    def verify_signature(self, message: bytes, signature: bytes) -> bool:
        """Verify a signature produced by this vault."""
        if _CRYPTO_AVAILABLE:
            from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
            try:
                pub = Ed25519PublicKey.from_public_bytes(self.keypair.public_key_bytes)
                pub.verify(signature, message)
                return True
            except Exception:
                return False
        sig = hmac.new(self.keypair.private_key_bytes, message, hashlib.sha256).digest()
        return hmac.compare_digest(sig, signature)

    def export_public_identity(self) -> dict[str, Any]:
        """Export a privacy-safe public identity bundle."""
        return {
            'session_id': self.session_id,
            'did': self.did_document().did,
            'npub': self.nostr_identity().npub,
            'committed_attributes': self.list_committed_attributes(),
        }
