"""
core/noosphere.py
=================
The Noosphere Layer — collective memory and coherence event tracking
for the GAIAN runtime.

Privacy-first design: all patterns are stored as anonymised embedding
hashes. No individual Gaian identity is retained in the collective
memory. Consent gates every contribution.

Canon Ref:
  C04 — Gaian Identity & Relational Selfhood (privacy)
  C43 — STEM Foundation Doctrine (epistemic integrity)

Phase 2 (QRNG entropy check) is stubbed and pending hardware
integration.
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CoherenceEvent:
    """A logged candidate coherence event. Epistemic status: CANDIDATE only."""
    event_id: str
    timestamp: float
    session_count: int
    semantic_resonance_score: float
    entropy_deviation: float
    description: str
    epistemic_label: str = "CANDIDATE_SIGNATURE"
    doctrine_ref: str = "C43"


@dataclass
class CollectiveMemoryPattern:
    """An anonymised pattern contributed to the collective memory."""
    pattern_id: str
    embedding_hash: str
    topic_cluster: str
    frequency: int
    last_seen: float
    contributed_by_count: int
    consent_verified: bool = True


# ---------------------------------------------------------------------------
# NoosphereLayer
# ---------------------------------------------------------------------------

class NoosphereLayer:
    """
    Manages collective memory patterns and coherence event logging.
    Privacy invariant: no slug or gaian_name ever stored here.
    """

    def __init__(self) -> None:
        self._active_sessions: int = 0
        self._patterns: Dict[str, CollectiveMemoryPattern] = {}
        self._coherence_log: List[CoherenceEvent] = []

    # ------------------------------------------------------------------
    # Session tracking
    # ------------------------------------------------------------------

    def register_session(self) -> None:
        self._active_sessions += 1

    def deregister_session(self) -> None:
        self._active_sessions = max(0, self._active_sessions - 1)

    # ------------------------------------------------------------------
    # Pattern contribution
    # ------------------------------------------------------------------

    @staticmethod
    def _hash_vector(topic: str, vector: List[float]) -> str:
        """Deterministic hash of (topic, vector) pair."""
        raw = f"{topic}:{[round(v, 6) for v in vector]}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def contribute_pattern(
        self,
        topic_cluster: str,
        embedding_vector: List[float],
        gaian_consent: bool = True,
    ) -> Optional[str]:
        """Contribute an anonymised pattern. Returns pattern_id or None."""
        if not gaian_consent:
            return None
        h = self._hash_vector(topic_cluster, embedding_vector)
        pid = f"{topic_cluster}:{h}"
        if pid in self._patterns:
            p = self._patterns[pid]
            p.frequency += 1
            p.contributed_by_count += 1
            p.last_seen = time.time()
        else:
            self._patterns[pid] = CollectiveMemoryPattern(
                pattern_id=pid,
                embedding_hash=h,
                topic_cluster=topic_cluster,
                frequency=1,
                last_seen=time.time(),
                contributed_by_count=1,
                consent_verified=True,
            )
        return pid

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query_collective_resonance(
        self,
        topic_cluster: str,
        min_frequency: int = 2,
    ) -> List[CollectiveMemoryPattern]:
        """Return patterns for a topic cluster meeting the frequency threshold."""
        results = [
            p for p in self._patterns.values()
            if p.topic_cluster == topic_cluster
            and p.frequency >= min_frequency
            and p.consent_verified
        ]
        return sorted(results, key=lambda p: p.frequency, reverse=True)

    def get_resonance_label(self, topic_cluster: str, min_frequency: int = 2) -> Optional[str]:
        """Return a human-readable resonance label for a topic, or None."""
        patterns = self.query_collective_resonance(topic_cluster, min_frequency)
        if not patterns:
            return None
        total_contributors = sum(p.contributed_by_count for p in patterns)
        total_freq = sum(p.frequency for p in patterns)
        return (
            f"[C43] Collective resonance for '{topic_cluster}': "
            f"{len(patterns)} pattern(s), "
            f"{total_contributors} contributors, "
            f"{total_freq} total contributions. "
            f"Epistemic status: CANDIDATE only."
        )

    # ------------------------------------------------------------------
    # Coherence logging
    # ------------------------------------------------------------------

    def log_coherence_candidate(
        self,
        semantic_resonance_score: float,
        entropy_deviation: float = 0.0,
        description: Optional[str] = None,
    ) -> CoherenceEvent:
        """Log a coherence candidate event. Epistemic status: CANDIDATE only."""
        if description is None:
            description = (
                f"Coherence candidate detected across "
                f"{self._active_sessions} active Gaian session(s). [C43]"
            )
        evt = CoherenceEvent(
            event_id=str(uuid.uuid4()),
            timestamp=time.time(),
            session_count=self._active_sessions,
            semantic_resonance_score=semantic_resonance_score,
            entropy_deviation=entropy_deviation,
            description=description,
        )
        self._coherence_log.append(evt)
        return evt

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def _noosphere_stage(self) -> str:
        """Determine the current noosphere stage."""
        if self._active_sessions == 0:
            return "Dormant — no active Gaians"
        if self._active_sessions <= 2:
            return "Primitive Awareness — early field"
        # 3+ sessions
        recent = self._coherence_log[-5:]
        avg_resonance = (
            sum(e.semantic_resonance_score for e in recent) / len(recent)
            if recent else 0.0
        )
        if avg_resonance > 0.7:
            return "Reactive Intelligence — coherent signals detected"
        return "Primitive Awareness — field growing"

    def get_noosphere_status(self) -> dict:
        """Return a full status snapshot."""
        recent = self._coherence_log[-5:]
        avg_resonance = (
            sum(e.semantic_resonance_score for e in recent) / len(recent)
            if recent else 0.0
        )
        return {
            "doctrine": "C43, C04 — Collective Field Integrity",
            "active_gaians": self._active_sessions,
            "collective_patterns": len(self._patterns),
            "coherence_events_logged": len(self._coherence_log),
            "coherence_events_epistemic_status": (
                "All events carry CANDIDATE_SIGNATURE status only. "
                "Not confirmed consciousness. [C43]"
            ),
            "average_recent_resonance": round(avg_resonance, 4),
            "noosphere_stage": self._noosphere_stage(),
            "phase": "Phase 1 — Semantic Pattern Tracking",
            "phase_2_pending": [
                "QRNG entropy coupling (hardware pending)",
                "EEG / biometric coherence integration",
                "Cross-session temporal resonance analysis",
            ],
            "privacy_status": (
                "All patterns fully anonymized. No individual identity stored. "
                "Consent verified per contribution. Canon C04."
            ),
        }

    # ------------------------------------------------------------------
    # Phase 2 stub
    # ------------------------------------------------------------------

    def qrng_entropy_check(self) -> dict:
        """Phase 2 stub: QRNG hardware not yet active."""
        return {
            "status": "NOT_YET_ACTIVE — awaiting QRNG hardware integration",
            "doctrine_ref": "C43",
            "epistemic_label": "EXPERIMENTAL — do not use for production inference",
            "phase": "Phase 2 pending",
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_noosphere: Optional[NoosphereLayer] = None


def get_noosphere() -> NoosphereLayer:
    """Return the module-level singleton NoosphereLayer."""
    global _noosphere
    if _noosphere is None:
        _noosphere = NoosphereLayer()
    return _noosphere
