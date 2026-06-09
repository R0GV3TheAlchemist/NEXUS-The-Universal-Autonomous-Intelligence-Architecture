"""Tests for IdentityVault — Issue #260."""
from __future__ import annotations

import pytest

from core.identity.identity_vault import (
    IdentityVault,
    SelectiveDisclosureProof,
    DIDDocument,
    NostrIdentity,
)


# ---------------------------------------------------------------------------
# Vault generation
# ---------------------------------------------------------------------------

class TestVaultGeneration:
    def test_generate_returns_vault(self) -> None:
        vault = IdentityVault.generate('test-session')
        assert isinstance(vault, IdentityVault)

    def test_keypair_not_empty(self) -> None:
        vault = IdentityVault.generate('test-session')
        assert len(vault.keypair.public_key_bytes) > 0
        assert len(vault.keypair.private_key_bytes) > 0

    def test_two_vaults_different_keys(self) -> None:
        v1 = IdentityVault.generate('s1')
        v2 = IdentityVault.generate('s2')
        assert v1.keypair.public_key_bytes != v2.keypair.public_key_bytes


# ---------------------------------------------------------------------------
# DID Document
# ---------------------------------------------------------------------------

class TestDIDDocument:
    def test_did_starts_with_did_key(self) -> None:
        vault = IdentityVault.generate('test')
        doc = vault.did_document()
        assert doc.did.startswith('did:key:z')

    def test_did_document_to_dict(self) -> None:
        vault = IdentityVault.generate('test')
        d = vault.did_document().to_dict()
        assert '@context' in d
        assert d['id'].startswith('did:key:')
        assert 'verificationMethod' in d

    def test_did_document_idempotent(self) -> None:
        vault = IdentityVault.generate('test')
        assert vault.did_document().did == vault.did_document().did


# ---------------------------------------------------------------------------
# Nostr Identity
# ---------------------------------------------------------------------------

class TestNostrIdentity:
    def test_nostr_npub_prefix(self) -> None:
        vault = IdentityVault.generate('test')
        nostr = vault.nostr_identity()
        assert nostr.npub.startswith('npub1')

    def test_nostr_pubkey_is_hex(self) -> None:
        vault = IdentityVault.generate('test')
        nostr = vault.nostr_identity()
        int(nostr.pubkey_hex, 16)  # Should not raise


# ---------------------------------------------------------------------------
# Selective disclosure / ZKP scaffold
# ---------------------------------------------------------------------------

class TestSelectiveDisclosure:
    def test_commit_and_verify(self) -> None:
        vault = IdentityVault.generate('test')
        vault.commit_attribute('name', 'R0GV3')
        proof = vault.disclosure_proof('name')
        assert proof is not None
        assert proof.verify('R0GV3')

    def test_wrong_value_fails_verify(self) -> None:
        vault = IdentityVault.generate('test')
        vault.commit_attribute('name', 'R0GV3')
        proof = vault.disclosure_proof('name')
        assert proof is not None
        assert not proof.verify('NotR0GV3')

    def test_committed_attributes_list(self) -> None:
        vault = IdentityVault.generate('test')
        vault.commit_attribute('name', 'R0GV3')
        vault.commit_attribute('location', 'earth')
        attrs = vault.list_committed_attributes()
        assert 'name' in attrs
        assert 'location' in attrs

    def test_no_raw_value_in_proof(self) -> None:
        vault = IdentityVault.generate('test')
        vault.commit_attribute('secret', 'my_secret')
        proof = vault.disclosure_proof('secret')
        assert proof is not None
        assert proof.revealed_value is None  # Never stored by default


# ---------------------------------------------------------------------------
# Signing
# ---------------------------------------------------------------------------

class TestSigning:
    def test_sign_and_verify(self) -> None:
        vault = IdentityVault.generate('test')
        msg = b'Hello GAIA'
        sig = vault.sign(msg)
        assert vault.verify_signature(msg, sig)

    def test_tampered_message_fails(self) -> None:
        vault = IdentityVault.generate('test')
        sig = vault.sign(b'original')
        assert not vault.verify_signature(b'tampered', sig)


# ---------------------------------------------------------------------------
# Public export
# ---------------------------------------------------------------------------

class TestPublicExport:
    def test_export_no_private_key(self) -> None:
        vault = IdentityVault.generate('test-export')
        export = vault.export_public_identity()
        assert 'private' not in str(export).lower()
        assert 'did' in export
        assert 'npub' in export
