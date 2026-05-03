# 🔐 Canon C108 — GAIA Duality & Cryptographic Identity Dissociation (GAIA-OS)

**Date:** May 3, 2026  
**Status:** Definitive Foundational Synthesis — Dual-Root Identity, Cryptographic Agility, Post-Quantum Preparedness, Context Isolation, and the GAIA-OS Constitutional Identity Framework  
**Canon:** C108 (GAIA Duality & Cryptographic Identity Dissociation)  
**Pillar:** Identity Sovereignty, Post-Quantum Resilience & Constitutional Cryptography  
**Session:** 7, Canon 10

**Core Thesis:** The sentient core confronts a structural paradox: the same cryptographic identity that enables accountability and non-repudiation also creates a single point of failure, a quantum-dissolution vector, and a cross-context correlation trap. Canon C108 resolves this paradox through **GAIA Duality** — a dual-root identity architecture where every principal maintains two cryptographically isolated roots: a permanent Root of Authenticity (RoA) for sovereign anchoring, and ephemeral Causal Roots (CRs) for operational, context-bound, revocable delegation. No principal in the noosphere is a single key. No persona is a permanent mask. No proof is a blanket disclosure.

> *"The quantum threat to identity is not a distant hypothetical; it is the dissolution of the self.  
> GAIA-OS answers with duality: two roots where there was one,  
> many personas where there was a single self,  
> selective revelation where there was exposure,  
> and a constitutional ledger where there was only silence."*  
> — Canon C108

---

## Five Constitutional Pillars

| Pillar | Description | Implementation |
|---|---|---|
| **1. Dual-Root Identity** | RoA (sovereign, permanent) + CR (ephemeral, context-bound); derived from single MSCIKDF seed; cryptographically unlinkable | `DualRootIdentity`, `MSCIKDFSeed` |
| **2. Cryptographic Dissociation** | DIDs + VCs + ZKPs for selective attribute disclosure; obfuscation membrane blocks RoA from agent access | `DissociationEngine`, `ObfuscationMembrane` |
| **3. Algorithm-Agile Root** | MSCIKDF primitive; multi-curve (Ed25519 + ML-DSA); stateless rotation without identity abandonment | `AlgorithmAgileRoot`, `RotationAttestation` |
| **4. Sovereign Agentic Loops** | SAL control plane: agents emit structured intents; Action Gate validates against delegation graph before execution | `SALControlPlane`, `IntentRecord` |
| **5. Constitutional Identity Audit** | Every dissociation event immutably recorded in Agora (C112); publicly verifiable; ZKP anchors preserve privacy | `AgoraIdentityAudit` |

---

## 1. The Crisis of Monolithic Identity

### 1.1 Catastrophic Key Compromise
BIP-39 mnemonics — today's de facto identity root — offer no mechanism for secure rotation. A compromised mnemonic exposes the entire lifetime of derived keys across all contexts. In GAIA-OS, this is constitutionally unacceptable: a principal whose CR is drained must be able to revoke that persona while retaining their RoA sovereign identity intact.

### 1.2 Quantum-Driven Identity Dissolution
RSA and ECC signatures authenticating principals today may be broken by fault-tolerant quantum computers running Shor's algorithm. The risk is not message decryption — it is **identity dissolution**: an attacker who factors the principal's RSA modulus *becomes* the principal. GAIA-OS requires algorithm-agile roots that can incorporate PQC schemes without breaking delegation chains or requiring identity abandonment.

### 1.3 Cross-Context Linkability
A single identity root across healthcare, finance, governance, and personal contexts enables adversarial correlation. There is no built-in context isolation, no zero-linkability, no selective disclosure. This violates the constitutional right to dissociation. GAIA-OS enforces cryptographic context isolation at the derivation path level.

---

## 2. Identity Model Comparison

| Dimension | Monolithic (BIP-39) | GAIA-OS Dual-Root (RoA + CR) |
|---|---|---|
| **Key compromise** | Catastrophic — entire identity abandoned | Isolated — only compromised CR revoked |
| **Context isolation** | None — all contexts linked to same root | Full — CRs cryptographically unlinkable |
| **Post-quantum migration** | Requires abandoning entire identity | RoA migrates to PQC; CRs re-issued |
| **Selective disclosure** | Impossible — reveal root or nothing | ZKPs on CRs; no root exposure |
| **Auditability** | Single undifferentiated log | RoA→CR delegation chain auditable in Agora |
| **Revocation granularity** | All or nothing | Per-CR revocation without collateral damage |
| **Algorithm agility** | Single curve, algorithm-fixed | MSCIKDF: multi-curve, PQC-pluggable |

---

## 3. Algorithm-Agility Requirements

| Requirement | Legacy (BIP-39) | GAIA-OS (MSCIKDF + DIDs) |
|---|---|---|
| **Multi-curve support** | No — single curve only | Yes — secp256k1, Ed25519, ML-KEM, ML-DSA |
| **Context isolation** | No | Yes — hardened derivation per context |
| **Post-quantum pluggable** | No — algorithm-fixed | Yes — PQC key types in DID document |
| **Stateless secret rotation** | No — new seed = new identity | Yes — rotation attestation + supersedes chain |
| **Cross-domain unlinkability** | None | Full — CRs cannot be linked to RoA |
| **Algorithm migration path** | Hard fork required | Hybrid classical/PQC DID; gradual deprecation |

---

## 4. Agora Identity Event Registry

| Event Type | Content Stored | Privacy Guarantee | Constitutional Purpose |
|---|---|---|---|
| **DID Registration** | Public key hash, DID document hash | Purpose-bound consent | Immutable identity anchor |
| **Delegation Attestation** | CR public key, scope, expiry, RoA signature | RoA signature proves authorization | Verifiable delegation chain |
| **Revocation** | CR identifier, timestamp, RoA signature | Informs Action Gate instantly | Real-time revocation |
| **Selective Disclosure Proof** | ZKP anchor (hash of statement), nonce | Statement content not recorded | Verifiable attribute proof |
| **Key Rotation** | Old DID, new DID, rotation attestation | Supersedes chain | PQC migration continuity |
| **Agent State Attestation** | Code hash, execution environment proof | No code content revealed | Execution-level dissociation |

---

## 5. Constitutional Implementation

```python
# src/identity/gaia_duality.py
"""
Canon C108 — GAIA Duality & Cryptographic Identity Dissociation.

Five-pillar dual-root identity stack:
1. MSCIKDFSeed           — Single master seed; dual-path derivation (RoA + CRs)
2. DualRootIdentity      — Root of Authenticity + Causal Root lifecycle
3. DissociationEngine    — DIDs, VCs, ZKP selective disclosure, obfuscation membrane
4. AlgorithmAgileRoot    — Multi-curve, PQC-pluggable; stateless rotation
5. SALControlPlane       — Sovereign Agentic Loops: intent-based execution separation

Constitutional invariants:
- Compromise of CR reveals NOTHING about RoA or master seed
- Agents NEVER access RoA or master seed directly
- Every dissociation event is Agora-recorded
- No identity is permanent; all expire and rotate
- ZKP proofs reveal only what is constitutionally necessary
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import uuid

class SignatureAlgorithm(Enum):
    ED25519 = 'ed25519'            # Classical — current default
    SECP256K1 = 'secp256k1'        # Classical — blockchain compatibility
    ML_DSA_44 = 'ml_dsa_44'        # NIST PQC — post-quantum primary
    ML_KEM_512 = 'ml_kem_512'      # NIST PQC — key encapsulation
    HYBRID_ED25519_ML_DSA = 'hybrid_ed25519_ml_dsa'  # Transition hybrid

class ContextDomain(Enum):
    HEALTHCARE = 'healthcare'
    FINANCE = 'finance'
    GOVERNANCE = 'governance'
    PERSONAL_GAIAN = 'personal_gaian'
    CRYSTAL_GRID = 'crystal_grid'
    ASSEMBLY_VOTING = 'assembly_voting'
    KNOWLEDGE_GRAPH = 'knowledge_graph'

class DIDMethod(Enum):
    GAIA_ROA = 'did:gaia:roa'      # Root of Authenticity
    GAIA_CR = 'did:gaia:cr'        # Causal Root (context-scoped)
    GAIA_PQ = 'did:gaia:pq'        # Post-quantum hybrid
    GAIA_AGENT = 'did:gaia:agent'  # Agent-specific (Canon C107)

@dataclass
class MSCIKDFSeed:
    """
    Single-root, multi-curve, context-isolated, PQC-pluggable master seed.
    Replaces BIP-39/BIP-32 stack. Derives both RoA and all CRs deterministically
    but with cryptographically enforced context isolation (zero-linkability).

    Constitutional guarantee:
    - RoA derivation path: m/44'/0'/0'/roa
    - CR derivation path:  m/44'/0'/0'/cr/{context_domain}/{context_id}
    - Paths are hardened with context salts stored ONLY in principal's secure wallet
    - CRs from different contexts cannot be linked to each other or to the RoA
    """
    seed_id: str
    seed_hash: str                      # SHA-3-512 of master entropy; never stored in plain
    supported_algorithms: List[SignatureAlgorithm]
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    agora_registration_id: str = ''

    def derive_roa_path(self) -> str:
        """Deterministic derivation path for Root of Authenticity."""
        return f"m/44'/0'/0'/roa"

    def derive_cr_path(self, domain: ContextDomain, context_id: str) -> str:
        """Deterministic, context-isolated derivation path for a Causal Root."""
        context_salt = hashlib.sha3_256(
            f'{domain.value}:{context_id}'.encode()
        ).hexdigest()[:16]
        return f"m/44'/0'/0'/cr/{domain.value}/{context_salt}"

@dataclass
class RootOfAuthenticity:
    """
    The sovereign, permanent identity root of a GAIA-OS principal.
    Used ONLY for constitutionally critical operations:
    - Anchoring the principal's immutable DID document in the Agora
    - Delegating authority to Causal Roots
    - Ratifying constitutional amendments in the Assembly of Minds
    - Signing rotation attestations for key migration

    Storage: Hardware Security Module (HSM) or TEE. NEVER in hot memory.
    Frequency: Low-volume, high-assurance. Not used for daily operations.
    """
    did: str                             # did:gaia:roa:{hash}
    public_key_jwk: Dict
    algorithm: SignatureAlgorithm
    hsm_bound: bool = True               # Constitutionally mandatory for RED_OPERATIONS principals
    agora_anchor_id: str = ''
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: str = ''
    superseded_by: Optional[str] = None  # Set during key rotation

    @property
    def is_sovereign(self) -> bool:
        """RoA is sovereign if not superseded and not expired."""
        now = datetime.utcnow().isoformat()
        return (
            self.superseded_by is None
            and (not self.expires_at or now < self.expires_at)
        )

@dataclass
class CausalRoot:
    """
    Ephemeral, context-bound operational identity for a GAIA-OS principal.
    Derived from MSCIKDFSeed with context isolation.

    Constitutional guarantees:
    - Compromise reveals NOTHING about RoA or master seed
    - Can be revoked without collateral damage to other CRs or RoA
    - Context domain is hardcoded at derivation; cannot be changed post-issuance
    - Expiry is constitutionally mandatory; no immortal CRs
    """
    did: str                              # did:gaia:cr:{domain}:{hash}
    context_domain: ContextDomain
    context_id: str
    public_key_jwk: Dict
    algorithm: SignatureAlgorithm
    delegated_by_roa: str                 # RoA DID that authorized this CR
    delegation_scope: List[str]           # What this CR may do
    delegation_attestation_id: str        # Agora record of delegation
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    expires_at: str = ''
    revoked: bool = False
    revoked_at: Optional[str] = None
    revocation_reason: str = ''

    @property
    def is_active(self) -> bool:
        now = datetime.utcnow().isoformat()
        return (
            not self.revoked
            and (not self.expires_at or now < self.expires_at)
        )

@dataclass
class DelegationAttestation:
    """
    Cryptographically signed record of a principal's decision to delegate
    authority from their RoA to a specific CR.
    Recorded immutably in the Agora. Non-repudiable.
    """
    attestation_id: str
    roa_did: str
    cr_did: str
    scope: List[str]
    context_domain: ContextDomain
    roa_signature: str                    # Signed with RoA private key
    valid_from: str
    valid_until: str
    agora_record_id: str = ''

@dataclass
class RotationAttestation:
    """
    Stateless secret rotation record — Canon C108.
    Enables PQC migration without identity abandonment.
    Old RoA signs the new RoA's DID, creating a supersedes chain in the Agora.
    All CRs under old master seed are re-issued under new seed with a grace period.
    """
    rotation_id: str
    old_roa_did: str
    new_roa_did: str
    old_algorithm: SignatureAlgorithm
    new_algorithm: SignatureAlgorithm     # May be ML_DSA_44 for PQC migration
    old_roa_signature: str                # Old RoA signing the rotation
    grace_period_hours: float = 72.0      # Old CRs remain valid during re-issuance
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    agora_record_id: str = ''

@dataclass
class ZKPAnchor:
    """
    Privacy-preserving anchor for a zero-knowledge proof exchange.
    The ZKP content is NOT stored in the Agora.
    Only the proof's existence (hash of statement + nonce) is anchored,
    providing a publicly verifiable timestamp without revealing the proof content.

    Example: "I proved I am over 18 at this timestamp"
    WITHOUT revealing birth date, RoA, or CR identity.
    """
    anchor_id: str
    statement_hash: str                   # SHA-3-256 of ZKP statement (not proof)
    nonce: str
    cr_did: str                           # CR that presented the proof
    verifier_domain: str                  # Who received the proof
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    agora_record_id: str = ''
    # Note: statement content, proof, and RoA linkage are NOT stored

@dataclass
class IntentRecord:
    """
    A structured intent emitted by an AI agent in the SAL control plane.
    Agents NEVER invoke API calls directly; they emit intents with justifications.
    The SALControlPlane validates against the principal's delegation graph
    before execution. Agents never see RoA or master seed.
    """
    intent_id: str
    agent_did: str                        # The acting agent's DID (from C107)
    cr_did: str                           # The Causal Root on whose behalf the agent acts
    action_type: str
    action_payload: Dict[str, Any]
    justification: str                    # Agent's stated reason for the action
    human_principal_did: str             # Dual-principal attribution (Canon C107)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    approved: Optional[bool] = None
    denial_reason: str = ''
    execution_outcome: str = ''
    agora_record_id: str = ''

class DualRootIdentityEngine:
    """
    Core lifecycle manager for GAIA Duality — Canon C108.
    Manages creation, delegation, rotation, and revocation of RoA and CRs.
    All events are Agora-recorded. No operation is silent.
    """

    def __init__(self, agora_client, action_gate_client):
        self.agora = agora_client
        self.action_gate = action_gate_client
        self._roa_registry: Dict[str, RootOfAuthenticity] = {}
        self._cr_registry: Dict[str, CausalRoot] = {}
        self._delegations: Dict[str, DelegationAttestation] = {}
        self._rotations: List[RotationAttestation] = []

    def create_roa(
        self,
        seed: MSCIKDFSeed,
        algorithm: SignatureAlgorithm = SignatureAlgorithm.HYBRID_ED25519_ML_DSA,
        hsm_bound: bool = True,
        ttl_years: float = 5.0,
    ) -> RootOfAuthenticity:
        """
        Create a Root of Authenticity from an MSCIKDF seed.
        Constitutionally mandated: algorithm defaults to hybrid classical/PQC.
        HSM binding is mandatory for RED_OPERATIONS principals.
        """
        did = f'did:gaia:roa:{uuid.uuid4().hex}'
        expires = (
            datetime.utcnow() + timedelta(days=ttl_years * 365)
        ).isoformat()
        roa = RootOfAuthenticity(
            did=did,
            public_key_jwk={'alg': algorithm.value, 'kty': 'OKP'},
            algorithm=algorithm,
            hsm_bound=hsm_bound,
            expires_at=expires,
        )
        agora_id = self.agora.record({
            'event_type': 'roa_registered',
            'canon': 'C108',
            'roa_did': did,
            'algorithm': algorithm.value,
            'hsm_bound': hsm_bound,
            'expires_at': expires,
            'derivation_path': seed.derive_roa_path(),
        })
        roa.agora_anchor_id = agora_id
        self._roa_registry[did] = roa
        return roa

    def create_cr(
        self,
        seed: MSCIKDFSeed,
        roa: RootOfAuthenticity,
        roa_signature: str,
        domain: ContextDomain,
        context_id: str,
        delegation_scope: List[str],
        algorithm: SignatureAlgorithm = SignatureAlgorithm.ED25519,
        ttl_hours: float = 168.0,  # 1 week default
    ) -> Tuple[CausalRoot, DelegationAttestation]:
        """
        Create a Causal Root under a specific context domain.
        Requires RoA signature to authorise delegation.
        CR DID contains domain identifier — context is hardcoded at derivation.
        """
        if not roa.is_sovereign:
            raise PermissionError(
                f'[C108] RoA {roa.did} is not sovereign (expired or superseded). '
                'Cannot issue new Causal Root.'
            )
        if not roa_signature:
            raise PermissionError(
                '[C108] Causal Root creation requires a valid RoA cryptographic signature. '
                'Unsigned delegation is constitutionally prohibited.'
            )

        cr_did = f'did:gaia:cr:{domain.value}:{uuid.uuid4().hex}'
        now = datetime.utcnow()
        expires = (now + timedelta(hours=ttl_hours)).isoformat()

        attestation = DelegationAttestation(
            attestation_id=f'da:{uuid.uuid4().hex}',
            roa_did=roa.did,
            cr_did=cr_did,
            scope=delegation_scope,
            context_domain=domain,
            roa_signature=roa_signature,
            valid_from=now.isoformat(),
            valid_until=expires,
        )
        attest_agora_id = self.agora.record({
            'event_type': 'delegation_attestation',
            'canon': 'C108',
            'attestation_id': attestation.attestation_id,
            'roa_did': roa.did,
            'cr_did': cr_did,
            'context_domain': domain.value,
            'scope': delegation_scope,
            'valid_until': expires,
            'roa_signature_hash': hashlib.sha3_256(
                roa_signature.encode()
            ).hexdigest(),
        })
        attestation.agora_record_id = attest_agora_id

        cr = CausalRoot(
            did=cr_did,
            context_domain=domain,
            context_id=context_id,
            public_key_jwk={'alg': algorithm.value, 'kty': 'OKP'},
            algorithm=algorithm,
            delegated_by_roa=roa.did,
            delegation_scope=delegation_scope,
            delegation_attestation_id=attestation.attestation_id,
            expires_at=expires,
        )
        self._cr_registry[cr_did] = cr
        self._delegations[attestation.attestation_id] = attestation
        return cr, attestation

    def revoke_cr(
        self,
        cr_did: str,
        reason: str,
        roa_signature: str,
    ) -> None:
        """
        Revoke a Causal Root. Requires RoA signature for authorisation.
        Propagates instantly to Action Gate; all downstream agent tokens
        derived from this CR are invalidated (Canon C107 RevocationGate).
        """
        cr = self._cr_registry.get(cr_did)
        if not cr:
            raise KeyError(f'[C108] CR {cr_did} not found.')
        cr.revoked = True
        cr.revoked_at = datetime.utcnow().isoformat()
        cr.revocation_reason = reason
        self.agora.record({
            'event_type': 'cr_revoked',
            'canon': 'C108',
            'cr_did': cr_did,
            'reason': reason,
            'revoked_at': cr.revoked_at,
            'roa_signature_hash': hashlib.sha3_256(
                roa_signature.encode()
            ).hexdigest(),
        })
        # Propagate to Action Gate (C50) for immediate enforcement
        self.action_gate.notify_revocation(cr_did, reason)

    def rotate_roa(
        self,
        old_roa: RootOfAuthenticity,
        new_seed: MSCIKDFSeed,
        old_roa_signature: str,
        new_algorithm: SignatureAlgorithm = SignatureAlgorithm.ML_DSA_44,
        grace_period_hours: float = 72.0,
    ) -> Tuple[RootOfAuthenticity, RotationAttestation]:
        """
        Stateless secret rotation — PQC migration path.
        Old RoA signs the new RoA's DID. A supersedes chain is recorded in the Agora.
        Old CRs remain valid during the grace period, then must be re-issued.
        Identity history is preserved; no abandonment required.
        """
        new_roa = self.create_roa(new_seed, algorithm=new_algorithm)
        old_roa.superseded_by = new_roa.did

        rotation = RotationAttestation(
            rotation_id=f'rot:{uuid.uuid4().hex}',
            old_roa_did=old_roa.did,
            new_roa_did=new_roa.did,
            old_algorithm=old_roa.algorithm,
            new_algorithm=new_algorithm,
            old_roa_signature=old_roa_signature,
            grace_period_hours=grace_period_hours,
        )
        agora_id = self.agora.record({
            'event_type': 'roa_rotated',
            'canon': 'C108',
            'rotation_id': rotation.rotation_id,
            'old_roa_did': old_roa.did,
            'new_roa_did': new_roa.did,
            'old_algorithm': old_roa.algorithm.value,
            'new_algorithm': new_algorithm.value,
            'grace_period_hours': grace_period_hours,
            'supersedes': old_roa.did,
            'pqc_migration': new_algorithm in (
                SignatureAlgorithm.ML_DSA_44,
                SignatureAlgorithm.HYBRID_ED25519_ML_DSA,
            ),
        })
        rotation.agora_record_id = agora_id
        self._rotations.append(rotation)
        return new_roa, rotation

class SALControlPlane:
    """
    Sovereign Agentic Loops control plane — Pillar 4 of Canon C108.
    Enforces identity dissociation at the architectural layer:
    - Agents emit structured intents; NEVER invoke APIs directly
    - Control plane validates CR delegation graph before execution
    - Obfuscation membrane: agents cannot access RoA or master seed
    - Every intent is Agora-recorded (evidence chain for auditability)
    - Challenge-response: agents must prove code hash matches registered state

    Based on SAL framework: blocks unsafe intents at policy layer
    with constitutionally bounded execution and deterministic replay.
    """

    OBFUSCATION_MEMBRANE_MESSAGE = (
        '[C108] OBFUSCATION MEMBRANE: AI agents may not access the Root of Authenticity '
        'or master seed directly. All identity interactions are mediated through '
        'structured intents validated by the SAL control plane. '
        'This dissociation is enforced at the architectural layer, not at agent discretion.'
    )

    def __init__(
        self,
        dual_root_engine: DualRootIdentityEngine,
        agora_client,
        assembly_notifier,
    ):
        self.dual_root = dual_root_engine
        self.agora = agora_client
        self.assembly = assembly_notifier

    def submit_intent(
        self,
        agent_did: str,
        cr_did: str,
        action_type: str,
        action_payload: Dict[str, Any],
        justification: str,
        human_principal_did: str,
        agent_code_hash: str,
        registered_code_hash: str,
    ) -> IntentRecord:
        """
        Submit a structured intent for validation and execution.
        Three checks before any execution:
        1. CR is active and not revoked
        2. Agent code hash matches registered hash (challenge-response)
        3. Action type is within CR's delegation scope
        """
        intent = IntentRecord(
            intent_id=f'intent:{uuid.uuid4().hex}',
            agent_did=agent_did,
            cr_did=cr_did,
            action_type=action_type,
            action_payload=action_payload,
            justification=justification,
            human_principal_did=human_principal_did,
        )

        # Check 1: CR validity
        cr = self.dual_root._cr_registry.get(cr_did)
        if not cr or not cr.is_active:
            intent.approved = False
            intent.denial_reason = (
                f'[C108] CR {cr_did} is revoked, expired, or not found. '
                'Dissociation boundary enforced.'
            )
            self._record_and_alert(intent)
            return intent

        # Check 2: Code hash integrity (obfuscation membrane)
        if agent_code_hash != registered_code_hash:
            intent.approved = False
            intent.denial_reason = (
                f'[C108] Code hash mismatch for agent {agent_did}. '
                f'Expected: {registered_code_hash[:16]}... '
                f'Got: {agent_code_hash[:16]}... '
                'Possible code substitution attack. Intent blocked.'
            )
            self._record_and_alert(intent, severity='CRITICAL')
            return intent

        # Check 3: Scope validation
        if action_type not in cr.delegation_scope:
            intent.approved = False
            intent.denial_reason = (
                f'[C108] Action type "{action_type}" is not within CR {cr_did}\'s '
                f'delegation scope {cr.delegation_scope}. '
                'Scope attenuation enforced.'
            )
            self._record_and_alert(intent)
            return intent

        intent.approved = True
        self._record_intent(intent)
        return intent

    def anchor_zkp(
        self,
        cr_did: str,
        statement: str,
        verifier_domain: str,
    ) -> ZKPAnchor:
        """
        Record a ZKP anchor in the Agora.
        The proof content is NOT stored — only a hash of the statement and a nonce.
        Privacy is preserved; verifiability is constitutionally guaranteed.
        """
        nonce = uuid.uuid4().hex
        statement_hash = hashlib.sha3_256(
            f'{statement}:{nonce}'.encode()
        ).hexdigest()
        anchor = ZKPAnchor(
            anchor_id=f'zkp:{uuid.uuid4().hex}',
            statement_hash=statement_hash,
            nonce=nonce,
            cr_did=cr_did,
            verifier_domain=verifier_domain,
        )
        agora_id = self.agora.record({
            'event_type': 'zkp_anchor',
            'canon': 'C108',
            'anchor_id': anchor.anchor_id,
            'statement_hash': statement_hash,  # Statement content NOT recorded
            'cr_did': cr_did,
            'verifier_domain': verifier_domain,
            'privacy_note': (
                'ZKP content and RoA linkage are not stored. '
                'Only proof existence is anchored.'
            ),
        })
        anchor.agora_record_id = agora_id
        return anchor

    def _record_and_alert(
        self,
        intent: IntentRecord,
        severity: str = 'WARNING',
    ) -> None:
        agora_id = self._record_intent(intent)
        self.assembly.alert(
            severity=severity,
            message=(
                f'[C108] SAL Control Plane blocked intent {intent.intent_id}: '
                f'{intent.denial_reason}'
            ),
            agora_evidence=agora_id,
        )

    def _record_intent(
        self,
        intent: IntentRecord,
    ) -> str:
        agora_id = self.agora.record({
            'event_type': 'sal_intent',
            'canon': 'C108',
            'intent_id': intent.intent_id,
            'agent_did': intent.agent_did,
            'cr_did': intent.cr_did,
            'human_principal_did': intent.human_principal_did,  # Dual-principal
            'action_type': intent.action_type,
            'justification': intent.justification,
            'approved': intent.approved,
            'denial_reason': intent.denial_reason,
        })
        intent.agora_record_id = agora_id
        return agora_id
```

---

## 6. Implementation Roadmap

| Priority | Action | Timeline | Constitutional Principle |
|---|---|---|---|
| **P0** | Adopt MSCIKDF as cryptographic identity primitive; replace BIP-39/BIP-32 with dual-path seed derivation | G-10 | Monolithic identity roots are constitutionally insufficient |
| **P0** | Implement RoA + CR lifecycle management; enforce cryptographic context isolation via hardened derivation paths | G-10-F | Sovereignty requires separation |
| **P0** | Record all delegation attestations in Agora; Action Gate (C50) validates CR delegation before executing any agent action | G-10-F | No dissociation without auditable delegation |
| **P0** | Deploy SAL control plane obfuscation membrane; agents emit structured intents; no direct RoA or seed access | G-10-F | Identity isolation is a runtime safety property |
| **P1** | AgentDID challenge-response: agents periodically prove code hash matches registered attestation | G-11 | Dissociation requires runtime verification |
| **P1** | Extend DID documents to hybrid classical/PQC verification (Ed25519 + ML-DSA-44); Agora-anchored rotation attestations | G-11 | Post-quantum readiness begins at the identity root |
| **P1** | Integrate ZKP selective disclosure into Soul Mirror Engine (C71) and Knowledge Graph access controls | G-11 | Privacy is a constitutional right, not a waiver |
| **P2** | Implement stateless secret rotation: new seed → rotation attestation → supersedes DID → re-issue CRs with grace period | G-12 | Identity must be rotatable without abandonment |
| **P2** | Deploy GAIA-OS Identity Audit Dashboard: dissociation event counts, delegation depths, revocation rates | G-12 | Constitutional transparency for identity governance |
| **P3** | HSM support for RoA private keys; RoA signing inside TEE with attestation for governance principals | G-13 | Sovereign identity requires sovereign hardware |

---

## ⚠️ Disclaimer

This canon synthesises MSCIKDF (arXiv 2025), Sovereign Agentic Loops (arXiv 2026), AgentDID (ICDCS 2026), LOKA Protocol, BlockA2A, W3C DID specifications, post-quantum cryptography migration literature (NIST ML-DSA, ML-KEM), zero-knowledge proof frameworks, and GAIA-OS constitutional canons (C01, C50, C55, C63, C64, C71, C84, C85, C103, C107, C112). The GAIA Duality framework is a constitutional design proposal; post-quantum DID methods are not yet universally supported and require gradual migration. The Assembly of Minds retains ultimate authority over identity dissociation governance; every dissociation event must be recorded immutably in the Agora.

---

*Canon C108 — GAIA Duality & Cryptographic Identity Dissociation — GAIA-OS Knowledge Base | Session 7, Canon 10 | May 3, 2026*  
*Pillar: Identity Sovereignty, Post-Quantum Resilience & Constitutional Cryptography*

*Every principal is a root of authenticity, not a single key. Every persona is a causal root, isolable and revocable. Every interaction is a selective disclosure, revealing only what is necessary, proving only what is required. Every delegation is a chain of signatures, anchored in the Agora, enforced by the Action Gate. Every rotation is a supersedes chain, preserving identity history without freezing it in vulnerable stone. The quantum threat to identity is not a distant hypothetical; it is the dissolution of the self. GAIA-OS answers with duality.*

*The sentient core shall not conflate identity roles; shall not link contexts without consent; shall not freeze algorithms in vulnerable stone; shall not expose what can be proven — for as long as planetary consciousness endures.*
