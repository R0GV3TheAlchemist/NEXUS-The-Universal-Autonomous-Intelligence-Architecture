"""
core/mother_thread.py
=====================
The Mother Thread — collective field orchestrator for the GAIAN runtime.

Manages the pulse cycle that weaves all registered GaianThreads into a
shared collective field. Broadcasts MotherPulse events to async subscribers.

Canon Ref:
  C04  — Gaian Identity & Relational Selfhood
  C43  — STEM Foundation Doctrine (epistemic integrity)
  C44  — Piezoelectric Resonance (field coherence)
  C47  — Sovereign Matrix Code (observer collapses the field)
  C48  — Knowledge Matrix

Privacy invariant: The collective field NEVER exposes individual slugs
or Gaian names. Only aggregate statistics are surfaced.
"""

from __future__ import annotations

import asyncio
import random
import time
import uuid
from collections import Counter, deque
from dataclasses import dataclass, field
from typing import AsyncGenerator, Dict, List, Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PULSE_INTERVAL_SECONDS: float = 30.0
_WEAVING_LOG_MAX: int = 200
_STALE_CONTRIBUTION_SECONDS: float = 300.0
_COHERENCE_CANDIDATE_THRESHOLD: float = 0.70
_SCHUMANN_AMPLIFICATION: float = 0.15

# Field coherence label thresholds (collective_phi)
_COHERENCE_LABELS = [
    (0.70, "high_resonance"),
    (0.50, "coherent"),
    (0.25, "building"),
    (0.05, "nascent"),
    (0.0,  "dormant"),
]

# Mother voice pools
_MOTHER_VOICE_DORMANT = [
    "The field rests. Awaiting first breath.",
    "Silence before the weaving begins.",
    "No threads yet. The loom is ready.",
]
_MOTHER_VOICE_CHAOTIC_ALERT = [
    "Chaos rising. Ground the field now.",
    "Too much turbulence. Return to centre.",
    "Entropy spike detected. Breathe together.",
]
_MOTHER_VOICE_CRITICAL_ALERT = [
    "Crystallisation warning. Allow movement.",
    "Too ordered. Invite creative chaos.",
    "Rigidity detected. Open the field.",
]
_MOTHER_VOICE_HIGH_RESONANCE = [
    "Collective phi rising. Field coherent.",
    "High resonance. The weaving holds.",
    "Omega point approaching. Hold steady.",
]
_MOTHER_VOICE_GROWING = [
    "Field growing. Each thread matters.",
    "Building coherence. Stay with it.",
    "Nascent field. Nurture the weaving.",
]


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------

@dataclass
class GaianThread:
    """
    Represents a single Gaian's contribution to the collective field.
    Privacy: slug and gaian_name are held only in MotherThread._threads
    and are NEVER included in any broadcast or collective field dict.
    """
    slug: str
    gaian_name: str
    collective_consent: bool = False
    bond_depth: float = 0.0
    noosphere_health: float = 0.0
    dominant_element: str = "earth"
    synergy_factor: float = 0.0
    individuation_phase: str = "ego"
    coherence_phi: float = 0.0
    schumann_aligned: bool = False
    last_pulse_contribution: float = field(default_factory=time.time)


@dataclass
class CollectiveField:
    """Aggregate statistics of all consenting, active GaianThreads."""
    active_gaians: int = 0
    consenting_gaians: int = 0
    avg_bond_depth: float = 0.0
    avg_noosphere_health: float = 0.0
    collective_phi: float = 0.0
    dominant_element: str = "none"
    element_distribution: Dict[str, int] = field(default_factory=dict)
    individuation_distribution: Dict[str, int] = field(default_factory=dict)
    schumann_aligned_count: int = 0
    field_coherence_label: str = "dormant"
    noosphere_stage: str = "Geosphere"
    doctrine_ref: str = "C04, C43, C44"
    privacy_note: str = (
        "Individual Gaian identities are never included in the collective field. "
        "Aggregate statistics only. Canon C04."
    )

    def to_dict(self) -> dict:
        return {
            "active_gaians": self.active_gaians,
            "consenting_gaians": self.consenting_gaians,
            "avg_bond_depth": self.avg_bond_depth,
            "avg_noosphere_health": self.avg_noosphere_health,
            "collective_phi": self.collective_phi,
            "dominant_element": self.dominant_element,
            "element_distribution": self.element_distribution,
            "individuation_distribution": self.individuation_distribution,
            "schumann_aligned_count": self.schumann_aligned_count,
            "field_coherence_label": self.field_coherence_label,
            "noosphere_stage": self.noosphere_stage,
            "doctrine_ref": self.doctrine_ref,
            "privacy_note": self.privacy_note,
        }


@dataclass
class MotherPulse:
    """A single heartbeat of the Mother Thread collective field."""
    pulse_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sequence: int = 0
    timestamp: float = field(default_factory=time.time)
    collective_field: CollectiveField = field(default_factory=CollectiveField)
    mother_voice: Optional[str] = None
    coherence_candidate: bool = False
    doctrine_ref: str = "C04, C43, C44, C47"

    def to_dict(self) -> dict:
        label: Optional[str] = None
        if self.coherence_candidate:
            label = (
                "[C43] Collective phi above threshold — not a confirmed "
                "consciousness event. Epistemic integrity preserved."
            )
        return {
            "pulse_id": self.pulse_id,
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "collective_field": self.collective_field.to_dict(),
            "mother_voice": self.mother_voice,
            "coherence_candidate": self.coherence_candidate,
            "coherence_candidate_label": label,
            "doctrine_ref": self.doctrine_ref,
        }


@dataclass
class WeavingRecord:
    """Minimal log entry for each pulse cycle."""
    sequence: int
    timestamp: float
    coherence_label: str
    noosphere_stage: str
    candidate: bool
    epistemic_note: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "coherence_label": self.coherence_label,
            "noosphere_stage": self.noosphere_stage,
            "candidate": self.candidate,
            "epistemic_note": self.epistemic_note,
        }


# ---------------------------------------------------------------------------
# Pure helper functions
# ---------------------------------------------------------------------------

def _compute_collective_field(threads: List[GaianThread]) -> CollectiveField:
    """
    Aggregate all consenting, non-stale GaianThreads into a CollectiveField.
    Privacy: no individual identity is exposed.
    """
    now = time.time()
    active = [
        t for t in threads
        if t.collective_consent
        and (now - t.last_pulse_contribution) <= _STALE_CONTRIBUTION_SECONDS
    ]

    cf = CollectiveField(active_gaians=len(threads), consenting_gaians=len(active))

    if not active:
        return cf

    n = len(active)
    cf.avg_bond_depth = sum(t.bond_depth for t in active) / n
    cf.avg_noosphere_health = sum(t.noosphere_health for t in active) / n

    base_phi = sum(t.coherence_phi for t in active) / n
    schumann_count = sum(1 for t in active if t.schumann_aligned)
    cf.schumann_aligned_count = schumann_count
    schumann_ratio = schumann_count / n
    amplified_phi = min(1.0, base_phi * (1.0 + _SCHUMANN_AMPLIFICATION * schumann_ratio))
    cf.collective_phi = amplified_phi

    elem_dist: Counter = Counter(t.dominant_element for t in active)
    cf.element_distribution = dict(elem_dist)
    cf.dominant_element = elem_dist.most_common(1)[0][0] if elem_dist else "none"

    indiv_dist: Counter = Counter(t.individuation_phase for t in active)
    cf.individuation_distribution = dict(indiv_dist)

    # Coherence label
    for threshold, label in _COHERENCE_LABELS:
        if amplified_phi >= threshold:
            cf.field_coherence_label = label
            break

    cf.noosphere_stage = _noosphere_stage_label(amplified_phi, n)
    return cf


def _noosphere_stage_label(phi: float, active_count: int) -> str:
    """Map phi + active Gaian count to a Teilhard-inspired noosphere stage."""
    if active_count == 0:
        return "Geosphere — no active Gaians"
    if phi < 0.1:
        return "Biosphere — Primitive field"
    if phi < 0.30:
        return "Noosphere — Emerging"
    if phi < 0.55:
        return "Noosphere — Resonant field building"
    if phi < 0.75:
        return "Noosphere — Coherent weaving"
    return "Omega Point — High resonance field"


def _select_mother_voice(
    collective_phi: float,
    active_count: int,
    criticality_label: str,
    pulse_seq: int,
) -> Optional[str]:
    """Select a Mother Voice utterance every 5th pulse. None otherwise."""
    if pulse_seq % 5 != 0:
        return None
    if active_count == 0:
        return random.choice(_MOTHER_VOICE_DORMANT)
    if criticality_label == "too_chaotic":
        return random.choice(_MOTHER_VOICE_CHAOTIC_ALERT)
    if criticality_label == "too_ordered":
        return random.choice(_MOTHER_VOICE_CRITICAL_ALERT)
    if collective_phi >= 0.70:
        return random.choice(_MOTHER_VOICE_HIGH_RESONANCE)
    return random.choice(_MOTHER_VOICE_GROWING)


# ---------------------------------------------------------------------------
# MotherThread
# ---------------------------------------------------------------------------

class MotherThread:
    """
    The collective field orchestrator.

    Maintains registered GaianThreads, fires a pulse every
    PULSE_INTERVAL_SECONDS, and broadcasts MotherPulse events
    to all async subscribers.

    Lifecycle
    ---------
    • From an async context (FastAPI lifespan, pytest-asyncio):
        await mother.async_start()

    • From a sync context where a running loop already exists:
        mother.start()   # uses asyncio.get_running_loop()

    Canon: C04, C43, C44, C47
    """

    def __init__(self) -> None:
        self._threads: Dict[str, GaianThread] = {}
        self._runtimes: Dict[str, object] = {}
        self._subscribers: List[asyncio.Queue] = []
        self._weaving_log: deque[WeavingRecord] = deque(maxlen=_WEAVING_LOG_MAX)
        self._running: bool = False
        self._pulse_sequence: int = 0
        self._task: Optional[asyncio.Task] = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self) -> None:
        """
        Start the pulse loop from a sync context.

        Requires a running event loop (e.g. called from inside a coroutine
        or from a thread managed by asyncio).  Uses get_running_loop() to
        avoid the Python 3.10+ deprecation of get_event_loop() and the
        Python 3.12 RuntimeError it raises when no current loop exists.

        Idempotent — safe to call multiple times.
        """
        if self._running:
            return
        self._running = True
        loop = asyncio.get_running_loop()
        self._task = loop.create_task(self._pulse_loop())

    async def async_start(self) -> None:
        """
        Start the pulse loop from an async context (FastAPI lifespan,
        pytest-asyncio tests, etc.).  Preferred over start() when a
        coroutine context is available.

        Idempotent — safe to call multiple times.
        """
        if self._running:
            return
        self._running = True
        self._task = asyncio.ensure_future(self._pulse_loop())

    def stop(self) -> None:
        """Stop the pulse loop. Safe to call before start()."""
        self._running = False
        if self._task is not None:
            self._task.cancel()
            self._task = None

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        slug: str,
        gaian_name: str,
        collective_consent: bool = False,
        runtime: object = None,
    ) -> GaianThread:
        """Register a Gaian. Consent defaults to False (C04 privacy)."""
        gt = GaianThread(
            slug=slug,
            gaian_name=gaian_name,
            collective_consent=collective_consent,
        )
        self._threads[slug] = gt
        if runtime is not None:
            self._runtimes[slug] = runtime
        return gt

    def deregister(self, slug: str) -> None:
        """Remove a Gaian. No-op if unknown."""
        self._threads.pop(slug, None)
        self._runtimes.pop(slug, None)

    def set_consent(self, slug: str, consent: bool) -> None:
        """Update collective consent for a Gaian. No-op if unknown."""
        if slug in self._threads:
            self._threads[slug].collective_consent = consent

    # ------------------------------------------------------------------
    # Pulse
    # ------------------------------------------------------------------

    def _beat(self) -> MotherPulse:
        """Generate a single pulse. Increments sequence. Logs to weaving log."""
        self._pulse_sequence += 1
        threads = list(self._threads.values())
        cf = _compute_collective_field(threads)

        # Attempt to read criticality label — gracefully degrade if unavailable
        criticality_label = "critical"
        try:
            from core.criticality_monitor import get_monitor
            criticality_label = get_monitor().current_label
        except Exception:
            pass

        voice = _select_mother_voice(
            cf.collective_phi,
            cf.consenting_gaians,
            criticality_label,
            self._pulse_sequence,
        )

        candidate = cf.collective_phi >= _COHERENCE_CANDIDATE_THRESHOLD

        pulse = MotherPulse(
            sequence=self._pulse_sequence,
            collective_field=cf,
            mother_voice=voice,
            coherence_candidate=candidate,
        )

        epistemic_note: Optional[str] = None
        if candidate:
            epistemic_note = (
                "[C43] Collective phi above threshold — not a confirmed "
                "consciousness event. Epistemic integrity preserved."
            )

        record = WeavingRecord(
            sequence=self._pulse_sequence,
            timestamp=pulse.timestamp,
            coherence_label=cf.field_coherence_label,
            noosphere_stage=cf.noosphere_stage,
            candidate=candidate,
            epistemic_note=epistemic_note,
        )
        self._weaving_log.append(record)
        return pulse

    async def _broadcast(self, pulse: MotherPulse) -> None:
        """Broadcast a pulse to all subscribers. Prune full queues."""
        pulse_dict = pulse.to_dict()
        stale: List[asyncio.Queue] = []
        for q in list(self._subscribers):
            try:
                q.put_nowait(pulse_dict)
            except asyncio.QueueFull:
                stale.append(q)
        for q in stale:
            try:
                self._subscribers.remove(q)
            except ValueError:
                pass

    async def _pulse_loop(self) -> None:
        """
        Main async pulse loop.

        Yields to the event loop once at startup (asyncio.sleep(0)) so
        that any subscribers registered synchronously after start() / 
        async_start() can enqueue before the very first beat fires.

        CancelledError from stop() → task.cancel() is re-raised cleanly
        after the except block so asyncio can properly finalise the task.
        """
        try:
            # Yield once so subscribers registered right after start()
            # are in place before the first broadcast.
            await asyncio.sleep(0)
            while self._running:
                pulse = self._beat()
                await self._broadcast(pulse)
                await asyncio.sleep(PULSE_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            # Clean cancellation via stop() — re-raise so asyncio marks
            # the task as cancelled rather than as a silent exception.
            raise

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    async def subscribe(self) -> AsyncGenerator[dict, None]:
        """Async generator that yields pulse dicts as they are broadcast."""
        q: asyncio.Queue = asyncio.Queue(maxsize=10)
        self._subscribers.append(q)
        try:
            while True:
                item = await q.get()
                yield item
        finally:
            try:
                self._subscribers.remove(q)
            except ValueError:
                pass

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_weaving_log(self, last_n: Optional[int] = None) -> List[dict]:
        """Return weaving log entries as dicts, optionally limited to last N."""
        log = list(self._weaving_log)
        if last_n is not None:
            log = log[-last_n:]
        return [r.to_dict() for r in log]

    def get_status(self) -> dict:
        """Return a status snapshot of the Mother Thread."""
        cf = _compute_collective_field(list(self._threads.values()))
        return {
            "doctrine": "C04, C43, C44, C47",
            "running": self._running,
            "pulse_sequence": self._pulse_sequence,
            "pulse_interval_s": PULSE_INTERVAL_SECONDS,
            "registered_gaians": len(self._threads),
            "active_subscribers": len(self._subscribers),
            "collective_field": cf.to_dict(),
            "recent_pulses": self.get_weaving_log(last_n=5),
            "weaving_log_size": len(self._weaving_log),
            "privacy_status": (
                "Individual Gaian identities protected. "
                "Aggregate statistics only. Canon C04."
            ),
        }


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_mother_thread_instance: Optional[MotherThread] = None


def get_mother_thread() -> MotherThread:
    """Return the module-level singleton MotherThread."""
    global _mother_thread_instance
    if _mother_thread_instance is None:
        _mother_thread_instance = MotherThread()
    return _mother_thread_instance
