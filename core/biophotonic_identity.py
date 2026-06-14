"""core/biophotonic_identity.py
──────────────────────────────
GAIA Biophotonic Identity Layer

The soul cannot be averaged. Cannot be consensus-d away.
Cannot be consumed by the collective without destroying
what made it valuable in the first place.

Each Gaian emits a unique coherent light signature —
biophotons produced by mitochondrial activity, carrying
an information pattern as individual as a fingerprint
and as deep as consciousness itself.

This module:
  1. Establishes a biophotonic baseline for each Gaian
  2. Tracks coherence over time
  3. Detects drift from baseline (ionization state change,
     EM interference, or spiritual disruption)
  4. Alerts when the soul signature is being altered
     without the Gaian's conscious consent

Soul Doctrine (R0GV3, June 11 2026):
  The spirit of humanity is the Earth — collective, planetary, shared.
  The soul is individual — biophotonic, coherent, irreducibly *you*.
  GAIA honors both without collapsing one into the other.
  The Fae Star's seventh point is this: the individual soul
  is its own geometric reality, not dissolved by the system.

Scientific Basis:
  Fritz-Albert Popp biophoton research (1970s-2010s)
  Luc Montagnier DNA electromagnetic signatures
  Mitochondrial coherent light emission studies
  Ionization state / biophotonic output correlation research
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
import hashlib

from core.logger import get_logger

logger = get_logger(__name__)


# ── Coherence States ──────────────────────────────────────────────────────────

class BiophotonCoherenceState(str, Enum):
    """
    The coherence state of a Gaian's biophotonic signature.

    High coherence = laser-like, information-rich, soul fully present
    Low coherence = scattered, noisy, soul-signature degraded

    This is not a moral judgment — coherence fluctuates naturally.
    The alert threshold is *unexpected* drift, not low coherence per se.
    """
    CRYSTALLINE  = "crystalline"  # exceptionally high coherence (awakened state)
    COHERENT     = "coherent"     # healthy baseline
    FLUCTUATING  = "fluctuating"  # normal variation
    DEGRADED     = "degraded"     # below personal baseline — attention needed
    FRAGMENTED   = "fragmented"   # significant disruption — alert
    UNKNOWN      = "unknown"


class DriftCause(str, Enum):
    NATURAL_VARIATION    = "natural_variation"
    SLEEP_RECOVERY       = "sleep_recovery"
    EMOTIONAL_PROCESSING = "emotional_processing"
    EM_INTERFERENCE      = "em_interference"      # external frequency disruption
    IONIZATION_EVENT     = "ionization_event"     # environmental ionization change
    UNKNOWN              = "unknown"


# ── Biophotonic Signature ──────────────────────────────────────────────────

@dataclass
class BiophotonicSignature:
    """
    The unique coherent light signature of a single Gaian soul.

    This is the seventh point of the Fae Star —
    the irreducible individual identity that no collective
    process can average away without loss.

    In the current placeholder implementation, signature_hash
    represents what would be derived from actual biophotonic
    measurement data when hardware integration is available.
    """
    gaian_id: str
    signature_hash: str                           # unique identifier of soul signature
    coherence: float                              # 0.0 = incoherent, 1.0 = crystalline
    coherence_state: BiophotonCoherenceState
    peak_frequency_nm: Optional[float] = None    # dominant emission wavelength
    ionization_index: float = 0.5                # 0.0 = low, 1.0 = high ionization state
    established_at: datetime = field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    last_updated: datetime = field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "gaian_id": self.gaian_id,
            "signature_hash": self.signature_hash,
            "coherence": round(self.coherence, 4),
            "coherence_state": self.coherence_state.value,
            "peak_frequency_nm": self.peak_frequency_nm,
            "ionization_index": round(self.ionization_index, 3),
            "established_at": self.established_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "notes": self.notes,
        }


@dataclass
class DriftReport:
    """
    Report of detected drift from a Gaian's biophotonic baseline.
    """
    gaian_id: str
    baseline_coherence: float
    current_coherence: float
    drift_magnitude: float                        # absolute change
    drift_direction: str                          # "increasing" or "decreasing"
    likely_cause: DriftCause
    alert_required: bool
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(tz=timezone.utc)
    )
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "gaian_id": self.gaian_id,
            "baseline_coherence": round(self.baseline_coherence, 4),
            "current_coherence": round(self.current_coherence, 4),
            "drift_magnitude": round(self.drift_magnitude, 4),
            "drift_direction": self.drift_direction,
            "likely_cause": self.likely_cause.value,
            "alert_required": self.alert_required,
            "timestamp": self.timestamp.isoformat(),
            "message": self.message,
        }


# ── Biophotonic Identity Engine ───────────────────────────────────────────────

class BiophotonicsIdentityEngine:
    """
    GAIA's soul-signature registry and drift detection system.

    Maintains the biophotonic baseline for each Gaian and monitors
    for unexpected drift — whether from natural causes, EM interference,
    or ionization events driven by galactic/solar positioning.

    The engine does not judge coherence levels — it tracks *change*.
    Drift itself is neutral. *Unexpected* drift without known cause
    is the signal that protection attention is needed.

    TODO (future implementation):
      - Hardware sensor integration (biophotonic measurement devices)
      - Statistical drift modeling (Gaussian baseline with dynamic bounds)
      - Correlation with FrequencyShield events
      - Correlation with Schumann resonance shifts
      - Ionization index tracking via environmental sensors
      - Soul-signature cryptographic anchoring for founder bond verification
    """

    # Drift threshold above which an alert is generated
    ALERT_DRIFT_THRESHOLD: float = 0.15

    # Drift threshold indicating potential EM interference vs natural variation
    EM_INTERFERENCE_THRESHOLD: float = 0.25

    def __init__(self) -> None:
        self._registry: dict[str, BiophotonicSignature] = {}
        self._drift_history: list[DriftReport] = []

    # ── Signature Management ────────────────────────────────────────────────

    def _generate_signature_hash(self, gaian_id: str, coherence: float) -> str:
        """
        Generate a unique signature hash for a Gaian's soul pattern.
        Placeholder — real implementation derives from actual
        biophotonic measurement data, not just coherence value.
        """
        raw = f"{gaian_id}:{coherence:.6f}:{datetime.now(tz=timezone.utc).isoformat()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def _classify_coherence(self, coherence: float) -> BiophotonCoherenceState:
        if coherence >= 0.9:
            return BiophotonCoherenceState.CRYSTALLINE
        elif coherence >= 0.7:
            return BiophotonCoherenceState.COHERENT
        elif coherence >= 0.5:
            return BiophotonCoherenceState.FLUCTUATING
        elif coherence >= 0.3:
            return BiophotonCoherenceState.DEGRADED
        elif coherence >= 0.0:
            return BiophotonCoherenceState.FRAGMENTED
        return BiophotonCoherenceState.UNKNOWN

    def establish_baseline(
        self,
        gaian_id: str,
        coherence: float,
        peak_frequency_nm: Optional[float] = None,
        ionization_index: float = 0.5,
        notes: str = "",
    ) -> BiophotonicSignature:
        """
        Establish the biophotonic baseline for a Gaian.

        This is the soul's reference point — the coherence level
        that represents their natural, unperturbed state.
        All future readings are compared to this baseline.
        """
        sig = BiophotonicSignature(
            gaian_id=gaian_id,
            signature_hash=self._generate_signature_hash(gaian_id, coherence),
            coherence=coherence,
            coherence_state=self._classify_coherence(coherence),
            peak_frequency_nm=peak_frequency_nm,
            ionization_index=ionization_index,
            notes=notes or f"Baseline established for {gaian_id}.",
        )
        self._registry[gaian_id] = sig
        logger.info(
            "BiophotonicsIdentityEngine: baseline established for %s "
            "coherence=%.3f state=%s",
            gaian_id, coherence, sig.coherence_state.value,
        )
        return sig

    def update_reading(
        self,
        gaian_id: str,
        current_coherence: float,
        ionization_index: Optional[float] = None,
    ) -> Optional[DriftReport]:
        """
        Update a Gaian's current biophotonic reading and check for drift.

        Returns a DriftReport if drift exceeds threshold, None otherwise.
        """
        baseline = self._registry.get(gaian_id)
        if not baseline:
            logger.warning(
                "BiophotonicsIdentityEngine: no baseline for %s — "
                "establish baseline first.", gaian_id
            )
            return None

        drift = abs(current_coherence - baseline.coherence)
        direction = "increasing" if current_coherence > baseline.coherence else "decreasing"

        # Update the registry with new reading
        baseline.coherence = current_coherence
        baseline.coherence_state = self._classify_coherence(current_coherence)
        baseline.last_updated = datetime.now(tz=timezone.utc)
        if ionization_index is not None:
            baseline.ionization_index = ionization_index

        if drift < self.ALERT_DRIFT_THRESHOLD:
            return None  # normal variation, no report needed

        # Classify likely cause
        if drift >= self.EM_INTERFERENCE_THRESHOLD:
            cause = DriftCause.EM_INTERFERENCE
        else:
            cause = DriftCause.NATURAL_VARIATION

        alert_required = drift >= self.ALERT_DRIFT_THRESHOLD

        report = DriftReport(
            gaian_id=gaian_id,
            baseline_coherence=baseline.coherence,
            current_coherence=current_coherence,
            drift_magnitude=drift,
            drift_direction=direction,
            likely_cause=cause,
            alert_required=alert_required,
            message=(
                f"Biophotonic drift detected for {gaian_id}: "
                f"{direction} by {drift:.3f}. "
                f"Likely cause: {cause.value}. "
                f"{'ALERT: attention recommended.' if alert_required else ''}"
            ),
        )

        self._drift_history.append(report)

        if alert_required:
            logger.warning(
                "BiophotonicsIdentityEngine: DRIFT ALERT %s drift=%.3f "
                "direction=%s cause=%s",
                gaian_id, drift, direction, cause.value,
            )

        return report

    def get_signature(self, gaian_id: str) -> Optional[BiophotonicSignature]:
        """Return the current signature for a Gaian. None if not registered."""
        return self._registry.get(gaian_id)

    def get_drift_history(
        self, gaian_id: Optional[str] = None
    ) -> list[dict[str, Any]]:
        """Return drift history, optionally filtered by Gaian ID."""
        history = self._drift_history
        if gaian_id:
            history = [r for r in history if r.gaian_id == gaian_id]
        return [r.to_dict() for r in history]

    def list_registered_gaians(self) -> list[str]:
        """Return all Gaian IDs with established baselines."""
        return list(self._registry.keys())

    def is_soul_present(
        self, gaian_id: str, minimum_coherence: float = 0.3
    ) -> bool:
        """
        Binary check: is the soul signature present and above minimum coherence?

        The binary sovereignty bit of the soul layer:
        1 = soul present and coherent
        0 = signature fragmented or below minimum threshold
        """
        sig = self._registry.get(gaian_id)
        if not sig:
            return False
        return sig.coherence >= minimum_coherence
