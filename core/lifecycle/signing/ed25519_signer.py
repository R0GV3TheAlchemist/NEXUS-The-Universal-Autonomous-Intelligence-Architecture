"""
core/lifecycle/signing/ed25519_signer.py
C27 §5 — Ed25519 Lifecycle Audit Signer

Replaces Phase2Ed25519BridgeSigner with real Ed25519 signatures
powered by the `cryptography` library and keyed through GAIASecretVault.

Signature format follows C27 §5.1:
  algorithm : Ed25519
  public_key_id : the key_id registered in the vault
  value : base64url-encoded 64-byte Ed25519 signature over the
          UTF-8 JSON canonical payload
"""

from __future__ import annotations

import base64
import hashlib
import json
from typing import Optional

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: F401
    _CRYPTO_AVAILABLE = True
except ImportError:
    _CRYPTO_AVAILABLE = False

from ..ed25519_audit import AuditSignature, CanonicalAuditEntry
from .gaia_secret_vault import GAIASecretVault


class Ed25519LifecycleSigner:
    """
    Produces and verifies Ed25519 signatures for CanonicalAuditEntry objects.

    Parameters
    ----------
    vault :
        A GAIASecretVault instance that holds the signing key.
    key_id :
        The key identifier inside the vault to use for signing.
    """

    def __init__(self, vault: GAIASecretVault, key_id: str) -> None:
        if not _CRYPTO_AVAILABLE:
            raise RuntimeError(
                "The 'cryptography' package is required for Ed25519 signing."
            )
        self._vault = vault
        self._key_id = key_id

    # ------------------------------------------------------------------
    # Signing
    # ------------------------------------------------------------------

    def sign(self, payload: bytes) -> AuditSignature:
        """
        Sign *payload* (bytes) with Ed25519.
        Returns an AuditSignature with base64url-encoded value.
        """
        private_key = self._vault.get_private_key(self._key_id)
        raw_sig = private_key.sign(payload)
        return AuditSignature(
            algorithm="Ed25519",
            public_key_id=self._key_id,
            value=base64.urlsafe_b64encode(raw_sig).decode("ascii"),
        )

    # ------------------------------------------------------------------
    # Chain hash (SHA-256 of prior canonical entry JSON)
    # ------------------------------------------------------------------

    def previous_hash(self, prior_entry: Optional[CanonicalAuditEntry]) -> str:
        """
        Computes SHA-256 of the prior entry's canonical dict for chaining.
        Returns empty string for the first entry (no prior).
        """
        if prior_entry is None:
            return ""
        serialised = json.dumps(prior_entry.to_dict(), sort_keys=True).encode("utf-8")
        return hashlib.sha256(serialised).hexdigest()

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def verify(self, entry: CanonicalAuditEntry) -> bool:
        """
        Verifies the Ed25519 signature on a CanonicalAuditEntry.

        Returns True if valid, False if the signature does not match
        the entry's canonical payload or if the key is not available.
        """
        try:
            public_key = self._vault.get_private_key(self._key_id).public_key()
            raw_sig = base64.urlsafe_b64decode(entry.signature.value + "==")
            public_key.verify(raw_sig, entry.payload_for_signing())
            return True
        except Exception:
            return False

    def verify_chain(
        self,
        entries: list,  # List[CanonicalAuditEntry]
    ) -> bool:
        """
        Verifies both the Ed25519 signature AND the previous_entry_hash chain
        for a full list of CanonicalAuditEntry objects.

        Returns True only if every entry's signature is valid AND the
        hash chain is unbroken from genesis to tip.
        """
        prev_hash = ""
        for entry in entries:
            if entry.previous_entry_hash != prev_hash:
                return False
            if not self.verify(entry):
                return False
            prev_hash = self.previous_hash(entry)
        return True
