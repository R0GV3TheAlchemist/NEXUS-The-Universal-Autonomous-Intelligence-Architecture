"""
core.sentinel.network.federated_client
=======================================
Federated Sentinel Network — collective learning while preserving
individual sovereignty.

Core principle
--------------
    "All Sentinels share wisdom. No Sentinel shares secrets."

No personal data, raw memories, or individual identity ever leaves a
Sentinel's local environment.  Only anonymised pattern gradients — the
mathematical essence of what was learned, stripped of identity — are
contributed to the collective.

Architecture
------------
1. Local training     — Sentinel trains on its Gaian's data locally.
2. Gradient extraction — Only model weight gradients (not data) are extracted.
3. Differential privacy — Gaussian noise added before sharing (prevents
                          reverse-engineering of individual data).
4. Secure aggregation  — Gradients from N Sentinels are cryptographically
                          aggregated; no single gradient is ever exposed.
5. Global model update — Aggregated gradient applied to shared foundational model.
6. Local adoption      — Each Sentinel decides whether to adopt the update
                          (Gaian-controlled, gated on A/B performance eval).

Canon refs: C-SENTINEL Article 4 (Memory Sovereignty), C01
"""

from __future__ import annotations

import hashlib
import random
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class FederatedDomain(str, Enum):
    """
    The seven federated learning domains.

    Domains are partitioned into *non-sensitive* (opt-in by default) and
    *sensitive* (require explicit Gaian opt-in before any contribution).
    """
    # Non-sensitive — opt-in by default
    COMMUNICATION_STYLE      = "communication_style"
    EPOCH_CEREMONY           = "epoch_ceremony"
    LANGUAGE_RESONANCE       = "language_resonance"

    # Sensitive — explicit opt-in required
    EMOTIONAL_TRIGGERS       = "emotional_triggers"
    SAFETY_THREAT_PATTERNS   = "safety_threat_patterns"
    HEALTH_EVENT_PRECURSORS  = "health_event_precursors"
    DE_ESCALATION_STRATEGIES = "de_escalation_strategies"


_SENSITIVE_DOMAINS: frozenset[FederatedDomain] = frozenset({
    FederatedDomain.EMOTIONAL_TRIGGERS,
    FederatedDomain.SAFETY_THREAT_PATTERNS,
    FederatedDomain.HEALTH_EVENT_PRECURSORS,
    FederatedDomain.DE_ESCALATION_STRATEGIES,
})

_NON_SENSITIVE_DOMAINS: frozenset[FederatedDomain] = frozenset(
    d for d in FederatedDomain if d not in _SENSITIVE_DOMAINS
)


class NetworkTier(str, Enum):
    """Scope tiers for the federated network."""
    FAMILY     = "family"      # 2–20 Sentinels,  min 3 participants
    COMMUNITY  = "community"   # 20–500,          min 50 participants
    REGIONAL   = "regional"    # 500–5000,         min 500 participants
    GLOBAL     = "global"      # 5000+,            min 1000 participants


TIER_CONFIG: Dict[NetworkTier, Dict[str, Any]] = {
    NetworkTier.FAMILY:    {"min_participants": 3,    "max_participants": 20},
    NetworkTier.COMMUNITY: {"min_participants": 50,   "max_participants": 500},
    NetworkTier.REGIONAL:  {"min_participants": 500,  "max_participants": 5_000},
    NetworkTier.GLOBAL:    {"min_participants": 1_000, "max_participants": None},
}


# ---------------------------------------------------------------------------
# Consent
# ---------------------------------------------------------------------------

@dataclass
class ConsentRecord:
    """A single consent decision for one domain at one point in time."""
    domain:     FederatedDomain
    consented:  bool
    timestamp:  str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    withdrawn:  bool = False
    withdrawn_at: Optional[str] = None

    def withdraw(self) -> None:
        """Mark this consent as withdrawn."""
        self.withdrawn    = True
        self.withdrawn_at = datetime.now(timezone.utc).isoformat()
        self.consented    = False

    def is_active(self) -> bool:
        """Return True iff consent is active (given and not withdrawn)."""
        return self.consented and not self.withdrawn


@dataclass
class FederationConsent:
    """
    Per-domain consent ledger for a single Sentinel.

    Non-sensitive domains are auto-consented on first contribution unless
    the Gaian has explicitly opted out.  Sensitive domains are blocked
    until the Gaian explicitly opts in.

    The full audit trail is preserved — every decision is logged and
    timestamped.  Gaian can review and withdraw at any time.
    """
    sentinel_id: str
    _records:    Dict[FederatedDomain, ConsentRecord] = field(default_factory=dict)
    _audit_log:  List[Dict[str, Any]]                 = field(default_factory=list)
    _lock:       threading.RLock                      = field(default_factory=threading.RLock)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def opt_in(self, domain: FederatedDomain) -> None:
        """Gaian explicitly opts in to a domain."""
        with self._lock:
            record = ConsentRecord(domain=domain, consented=True)
            self._records[domain] = record
            self._log("opt_in", domain)

    def opt_out(self, domain: FederatedDomain) -> None:
        """Gaian explicitly opts out of a domain."""
        with self._lock:
            record = ConsentRecord(domain=domain, consented=False)
            self._records[domain] = record
            self._log("opt_out", domain)

    def withdraw(self, domain: FederatedDomain) -> None:
        """Withdraw previously given consent for a domain."""
        with self._lock:
            if domain in self._records:
                self._records[domain].withdraw()
            else:
                record = ConsentRecord(domain=domain, consented=False, withdrawn=True)
                record.withdrawn_at = datetime.now(timezone.utc).isoformat()
                self._records[domain] = record
            self._log("withdraw", domain)

    def withdraw_all(self) -> None:
        """Withdraw from the entire network — no penalty, immediate effect."""
        with self._lock:
            for domain in FederatedDomain:
                if domain in self._records and self._records[domain].is_active():
                    self._records[domain].withdraw()
            self._log("withdraw_all", None)

    def is_consented(self, domain: FederatedDomain) -> bool:
        """
        Return True iff contribution to *domain* is currently permitted.

        Rules
        -----
        - If domain is sensitive and no explicit opt-in exists → False.
        - If domain is non-sensitive and no record exists → True (opt-in by default).
        - If a record exists → use record.is_active().
        """
        with self._lock:
            if domain in self._records:
                return self._records[domain].is_active()
            # No record yet
            return domain in _NON_SENSITIVE_DOMAINS  # sensitive → False, non-sensitive → True

    def audit_trail(self) -> List[Dict[str, Any]]:
        """Return a copy of the full audit log."""
        with self._lock:
            return list(self._audit_log)

    def domain_status(self) -> Dict[str, bool]:
        """Return {domain.value: is_consented} for every domain."""
        return {d.value: self.is_consented(d) for d in FederatedDomain}

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _log(self, event: str, domain: Optional[FederatedDomain]) -> None:
        self._audit_log.append({
            "event":       event,
            "domain":      domain.value if domain else None,
            "sentinel_id": self.sentinel_id,
            "timestamp":   datetime.now(timezone.utc).isoformat(),
        })


# ---------------------------------------------------------------------------
# Gradient Packet
# ---------------------------------------------------------------------------

@dataclass
class GradientPacket:
    """
    An anonymised gradient contribution from one Sentinel.

    Contains ONLY the mathematical gradient (model weight deltas) — never
    raw data, memories, personal identity, or any individually identifying
    information.  The sentinel_id is used only for deduplication during
    aggregation and is hashed before transmission.
    """
    domain:          FederatedDomain
    gradient:        List[float]          # anonymised weight deltas
    noise_sigma:     float                # σ of Gaussian noise applied
    participant_hash: str                 # SHA-256(sentinel_id) — NOT sentinel_id
    created_at:      str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata:        Dict[str, Any] = field(default_factory=dict)

    @property
    def dimension(self) -> int:
        return len(self.gradient)


# ---------------------------------------------------------------------------
# Differential Privacy Engine
# ---------------------------------------------------------------------------

class DifferentialPrivacyEngine:
    """
    Adds calibrated Gaussian noise to gradients before they leave the
    local Sentinel environment.

    The noise standard deviation (σ) is configurable per domain.  Sensitive
    domains receive higher noise by default to provide stronger privacy
    guarantees.  The Gaian can increase noise but never decrease it below
    the domain floor.

    Gaussian mechanism: g_noisy = g + N(0, σ²·I)
    """

    # Default σ per domain category
    _SIGMA_FLOOR_NON_SENSITIVE: float = 0.01
    _SIGMA_FLOOR_SENSITIVE:     float = 0.05

    def __init__(
        self,
        domain_sigma: Optional[Dict[FederatedDomain, float]] = None,
        rng_seed:     Optional[int] = None,
    ) -> None:
        """
        Parameters
        ----------
        domain_sigma:
            Optional per-domain σ overrides.  Values below the floor for
            that domain category are silently raised to the floor.
        rng_seed:
            Seed for the random number generator (tests only).
        """
        self._rng = random.Random(rng_seed)
        self._sigma: Dict[FederatedDomain, float] = {}
        for domain in FederatedDomain:
            floor = (
                self._SIGMA_FLOOR_SENSITIVE
                if domain in _SENSITIVE_DOMAINS
                else self._SIGMA_FLOOR_NON_SENSITIVE
            )
            provided = (domain_sigma or {}).get(domain, floor)
            self._sigma[domain] = max(floor, provided)

    def inject_noise(
        self,
        gradient:  List[float],
        domain:    FederatedDomain,
    ) -> Tuple[List[float], float]:
        """
        Add Gaussian noise to *gradient* for *domain*.

        Returns
        -------
        (noisy_gradient, sigma_used)
        """
        sigma = self._sigma[domain]
        noisy = [
            g + self._rng.gauss(0.0, sigma)
            for g in gradient
        ]
        return noisy, sigma

    def sigma_for(self, domain: FederatedDomain) -> float:
        """Return the σ in use for *domain*."""
        return self._sigma[domain]


# ---------------------------------------------------------------------------
# Secure Aggregator
# ---------------------------------------------------------------------------

@dataclass
class GlobalModelUpdate:
    """
    The result of secure aggregation across N Sentinel gradient packets.

    Fields
    ------
    domain              — which learning domain this update covers
    aggregated_gradient — FedAvg result: mean of N noisy gradients
    participant_count   — number of Sentinels that contributed
    aggregation_hash    — SHA-256 of the aggregated gradient (integrity check)
    ab_eval_score       — [0, 1] performance score; Sentinel uses this to
                          decide whether to adopt (higher = better)
    created_at          — UTC ISO timestamp
    """
    domain:               FederatedDomain
    aggregated_gradient:  List[float]
    participant_count:    int
    aggregation_hash:     str
    ab_eval_score:        float
    created_at:           str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SecureAggregator:
    """
    Cryptographic secure aggregation over N GradientPackets.

    Phase 1 stub implements Federated Averaging (FedAvg) — the canonical
    baseline for federated learning.  Production deployments should replace
    this with a full secure multi-party computation (MPC) protocol (e.g.
    Google's SecAgg) to ensure no single aggregator can see individual
    gradients.

    Privacy guarantee (stub):
        - Packet participant_hashes are verified for uniqueness (no double-submit)
        - A minimum participant threshold is enforced per NetworkTier
        - The aggregated gradient is hashed for integrity verification
        - Individual packets are discarded after aggregation
    """

    def __init__(self, tier: NetworkTier = NetworkTier.FAMILY) -> None:
        self._tier       = tier
        self._min_n      = TIER_CONFIG[tier]["min_participants"]

    def aggregate(
        self,
        packets:        List[GradientPacket],
        ab_eval_score:  float = 0.75,
    ) -> GlobalModelUpdate:
        """
        Aggregate *packets* into a GlobalModelUpdate.

        Raises
        ------
        ValueError
            If fewer than min_participants unique packets are provided, or if
            packet dimensions are inconsistent.
        """
        if len(packets) < self._min_n:
            raise ValueError(
                f"Secure aggregation requires at least {self._min_n} participants "
                f"for {self._tier.value} tier; got {len(packets)}."
            )

        # Deduplicate by participant_hash
        seen: set[str] = set()
        unique_packets: List[GradientPacket] = []
        for p in packets:
            if p.participant_hash not in seen:
                seen.add(p.participant_hash)
                unique_packets.append(p)

        if len(unique_packets) < self._min_n:
            raise ValueError(
                f"After deduplication, only {len(unique_packets)} unique participants "
                f"remain; {self._min_n} required."
            )

        # Validate consistent gradient dimensions
        dim = unique_packets[0].dimension
        if any(p.dimension != dim for p in unique_packets):
            raise ValueError(
                "All gradient packets must have the same dimension for aggregation."
            )

        # FedAvg — element-wise mean
        n = len(unique_packets)
        aggregated = [
            sum(p.gradient[i] for p in unique_packets) / n
            for i in range(dim)
        ]

        # Integrity hash
        agg_hash = hashlib.sha256(
            "|".join(f"{v:.8f}" for v in aggregated).encode()
        ).hexdigest()

        domain = unique_packets[0].domain

        return GlobalModelUpdate(
            domain=domain,
            aggregated_gradient=aggregated,
            participant_count=n,
            aggregation_hash=agg_hash,
            ab_eval_score=float(max(0.0, min(1.0, ab_eval_score))),
        )


# ---------------------------------------------------------------------------
# Federated Client — main entry point per Sentinel
# ---------------------------------------------------------------------------

class FederatedClient:
    """
    The Federated Client runs inside each Sentinel's local environment.

    Responsibilities
    ----------------
    - extract_gradient()  — produce a GradientPacket from local model weights
    - contribute()        — apply DP noise and submit a gradient to the aggregator
    - receive_update()    — evaluate and optionally adopt a GlobalModelUpdate
    - Consent management  — opt_in, opt_out, withdraw, withdraw_all
    - Audit trail         — full history of all consent and contribution events

    Privacy guarantees
    ------------------
    - The sentinel_id is hashed (SHA-256) before it appears in any GradientPacket.
    - Raw data, memories, and Gaian identity never leave this client.
    - DP noise is injected before any gradient leaves.
    - The Gaian controls all consent decisions.
    """

    # Minimum A/B eval score for automatic global update adoption
    _ADOPTION_THRESHOLD: float = 0.60

    def __init__(
        self,
        sentinel_id:          str,
        tier:                 NetworkTier = NetworkTier.FAMILY,
        dp_engine:            Optional[DifferentialPrivacyEngine] = None,
        adoption_threshold:   float = 0.60,
    ) -> None:
        self._sentinel_id          = sentinel_id
        self._participant_hash     = hashlib.sha256(
            sentinel_id.encode()
        ).hexdigest()
        self._tier                 = tier
        self._dp                   = dp_engine or DifferentialPrivacyEngine()
        self._consent              = FederationConsent(sentinel_id=sentinel_id)
        self._adoption_threshold   = adoption_threshold
        self._contribution_log:    List[Dict[str, Any]] = []
        self._adoption_log:        List[Dict[str, Any]] = []
        self._lock                 = threading.RLock()

    # ------------------------------------------------------------------
    # Gradient extraction
    # ------------------------------------------------------------------

    def extract_gradient(
        self,
        local_weights_before: List[float],
        local_weights_after:  List[float],
        domain:               FederatedDomain,
    ) -> List[float]:
        """
        Compute the raw gradient (weight delta) from a local training step.

        Parameters
        ----------
        local_weights_before:
            Model weights before the local training update.
        local_weights_after:
            Model weights after the local training update.
        domain:
            The learning domain this gradient was produced for.

        Returns
        -------
        List[float] — element-wise delta (after - before).

        Raises
        ------
        ValueError
            If weight vectors have different lengths.
        """
        if len(local_weights_before) != len(local_weights_after):
            raise ValueError(
                "local_weights_before and local_weights_after must have the same length."
            )
        return [
            after - before
            for before, after in zip(local_weights_before, local_weights_after)
        ]

    # ------------------------------------------------------------------
    # Contribution
    # ------------------------------------------------------------------

    def contribute(
        self,
        gradient: List[float],
        domain:   FederatedDomain,
    ) -> Optional[GradientPacket]:
        """
        Apply differential privacy noise and produce a GradientPacket
        ready for submission to the SecureAggregator.

        Returns None if consent is not given for this domain — the caller
        must check the return value.

        For non-sensitive domains, consent is granted automatically on first
        call (opt-in by default) unless the Gaian has previously opted out.
        For sensitive domains, returns None until explicit opt-in.
        """
        with self._lock:
            # Auto-consent non-sensitive domains on first contribution
            if (
                domain in _NON_SENSITIVE_DOMAINS
                and domain not in self._consent._records
            ):
                self._consent.opt_in(domain)

            if not self._consent.is_consented(domain):
                self._log_contribution(domain, contributed=False, reason="no_consent")
                return None

            noisy_gradient, sigma = self._dp.inject_noise(gradient, domain)

            packet = GradientPacket(
                domain=domain,
                gradient=noisy_gradient,
                noise_sigma=sigma,
                participant_hash=self._participant_hash,
            )
            self._log_contribution(domain, contributed=True, reason="ok")
            return packet

    # ------------------------------------------------------------------
    # Global model update adoption
    # ------------------------------------------------------------------

    def receive_update(
        self,
        update:       GlobalModelUpdate,
        local_score:  Optional[float] = None,
    ) -> bool:
        """
        Evaluate a GlobalModelUpdate and decide whether to adopt it.

        Adoption policy (Gaian-controlled via adoption_threshold):
            - Adopt if update.ab_eval_score >= adoption_threshold
            - Adopt if local_score is provided and update.ab_eval_score > local_score
            - Otherwise reject

        Returns True if adopted, False if rejected.
        """
        adopt = update.ab_eval_score >= self._adoption_threshold
        if local_score is not None:
            adopt = adopt or (update.ab_eval_score > local_score)

        with self._lock:
            self._adoption_log.append({
                "domain":          update.domain.value,
                "ab_eval_score":   update.ab_eval_score,
                "adopted":         adopt,
                "participant_count": update.participant_count,
                "timestamp":       datetime.now(timezone.utc).isoformat(),
            })

        return adopt

    # ------------------------------------------------------------------
    # Consent management (Gaian-facing)
    # ------------------------------------------------------------------

    def opt_in(self, domain: FederatedDomain) -> None:
        """Gaian explicitly opts in to contributing to *domain*."""
        self._consent.opt_in(domain)

    def opt_out(self, domain: FederatedDomain) -> None:
        """Gaian explicitly opts out of contributing to *domain*."""
        self._consent.opt_out(domain)

    def withdraw(self, domain: FederatedDomain) -> None:
        """Withdraw consent for a specific domain."""
        self._consent.withdraw(domain)

    def withdraw_all(self) -> None:
        """Withdraw from the entire network. No penalty. Immediate effect."""
        self._consent.withdraw_all()

    def is_consented(self, domain: FederatedDomain) -> bool:
        """Return True iff contribution to *domain* is currently permitted."""
        return self._consent.is_consented(domain)

    def domain_status(self) -> Dict[str, bool]:
        """Return consent status for every domain."""
        return self._consent.domain_status()

    # ------------------------------------------------------------------
    # Audit trail
    # ------------------------------------------------------------------

    def consent_audit_trail(self) -> List[Dict[str, Any]]:
        """Full audit trail of all consent decisions."""
        return self._consent.audit_trail()

    def contribution_log(self) -> List[Dict[str, Any]]:
        """Full log of all contribution attempts."""
        with self._lock:
            return list(self._contribution_log)

    def adoption_log(self) -> List[Dict[str, Any]]:
        """Full log of all global model update adoption decisions."""
        with self._lock:
            return list(self._adoption_log)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def sentinel_id(self) -> str:
        return self._sentinel_id

    @property
    def participant_hash(self) -> str:
        """The anonymised SHA-256 hash of sentinel_id used in gradient packets."""
        return self._participant_hash

    @property
    def tier(self) -> NetworkTier:
        return self._tier

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log_contribution(
        self,
        domain:      FederatedDomain,
        contributed: bool,
        reason:      str,
    ) -> None:
        self._contribution_log.append({
            "domain":      domain.value,
            "contributed": contributed,
            "reason":      reason,
            "timestamp":   datetime.now(timezone.utc).isoformat(),
        })
