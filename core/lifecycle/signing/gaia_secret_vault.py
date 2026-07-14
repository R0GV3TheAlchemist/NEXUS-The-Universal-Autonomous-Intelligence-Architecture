"""
core/lifecycle/signing/gaia_secret_vault.py
C15 / C27 — GAIA Secret Vault Interface

Defines the abstract vault contract and an in-process implementation
for use before the full C15 vault service is wired.

In production, replace InProcessVault with a subclass that delegates
to the runtime secret store (e.g. HashiCorp Vault, AWS KMS, or the
GAIA-native credential store defined in C15).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,  # noqa: F401
        Ed25519PublicKey,   # noqa: F401
    )
    from cryptography.hazmat.primitives.serialization import (
        Encoding,
        PublicFormat,
        PrivateFormat,     # noqa: F401
        NoEncryption,      # noqa: F401
    )
    _CRYPTO_AVAILABLE = True
except ImportError:
    _CRYPTO_AVAILABLE = False
    Ed25519PrivateKey = object  # type: ignore[assignment,misc]
    Ed25519PublicKey = object   # type: ignore[assignment,misc]


class VaultKeyNotFoundError(KeyError):
    """Raised when a requested key_id is not present in the vault."""


class GAIASecretVault(ABC):
    """
    Abstract interface for the GAIA Secret Vault (C15).

    All lifecycle signing operations obtain keys through this interface
    so that the concrete key-store can be swapped without touching the
    signing layer.
    """

    @abstractmethod
    def get_private_key(self, key_id: str) -> object:
        """Return the private key object for *key_id*."""

    @abstractmethod
    def get_public_key_bytes(self, key_id: str) -> bytes:
        """Return the raw public key bytes (32-byte Ed25519 key) for *key_id*."""

    @abstractmethod
    def has_key(self, key_id: str) -> bool:
        """Return True if *key_id* exists in the vault."""


class InProcessVault(GAIASecretVault):
    """
    In-process key vault backed by the `cryptography` library.

    Suitable for tests and single-process deployments.
    Keys are generated deterministically from a seed per key_id OR
    generated fresh and stored in-memory.

    Usage::

        vault = InProcessVault()
        key_id = vault.generate_key("gaian-abc123")
        signer = Ed25519LifecycleSigner(vault=vault, key_id=key_id)
    """

    def __init__(self) -> None:
        if not _CRYPTO_AVAILABLE:
            raise RuntimeError(
                "The 'cryptography' package is required for Ed25519 signing. "
                "Install it with: pip install cryptography"
            )
        self._keys: Dict[str, "Ed25519PrivateKey"] = {}

    def generate_key(self, key_id: str) -> str:
        """
        Generate a fresh Ed25519 key pair and register it under *key_id*.
        Returns *key_id* for convenience.
        Idempotent: if the key already exists it is not replaced.
        """
        if key_id not in self._keys:
            self._keys[key_id] = Ed25519PrivateKey.generate()
        return key_id

    def get_private_key(self, key_id: str) -> "Ed25519PrivateKey":
        if key_id not in self._keys:
            raise VaultKeyNotFoundError(
                f"Key '{key_id}' not found in InProcessVault. "
                "Call generate_key() or load a key first."
            )
        return self._keys[key_id]

    def get_public_key_bytes(self, key_id: str) -> bytes:
        private_key = self.get_private_key(key_id)
        return private_key.public_key().public_bytes(
            encoding=Encoding.Raw,
            format=PublicFormat.Raw,
        )

    def has_key(self, key_id: str) -> bool:
        return key_id in self._keys
