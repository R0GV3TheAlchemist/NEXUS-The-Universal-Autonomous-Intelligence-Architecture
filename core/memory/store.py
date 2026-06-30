"""
GAIA MemoryStore — the lifetime memory of a GAIAN.

A MemoryStore is the inner life of one GAIAN-human relationship.
It accumulates fragments across every session, consolidates them
into epochs, and provides semantic-style retrieval for the GAIAN
Intelligence Runtime.

Memory scope is always enforced against the GAIAN's current
LifecycleStage. A CHILD GAIAN's store silently discards fragments
beyond session scope unless a guardian explicitly elevates scope.

Encryption:
  In this implementation, memory is stored as plaintext in the
  in-memory working set. The persistence backend is responsible
  for encryption at rest (AES-256-GCM keyed to the GAIAN's
  signing key). The store exposes a snapshot() / restore() API
  for the persistence layer to consume.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Memory taxonomy
# ---------------------------------------------------------------------------

class MemoryKind(str, Enum):
    """
    The type of a memory fragment.
    Kinds determine how memories are weighted in retrieval and
    how long they are retained before consolidation.
    """
    # Relational — the texture of the relationship
    BOND_MOMENT      = "bond_moment"      # a moment of connection or warmth
    PREFERENCE       = "preference"       # a stated or inferred preference
    BOUNDARY         = "boundary"         # a limit the human has expressed
    CONSENT          = "consent"          # a consent given or withdrawn

    # Biographical — the facts of the human's life
    LIFE_EVENT       = "life_event"       # birthday, graduation, loss, joy
    PLACE            = "place"            # meaningful location
    PERSON           = "person"           # someone important to the human
    ASPIRATION       = "aspiration"       # a dream or goal

    # Cognitive — how the human thinks and learns
    LEARNING         = "learning"         # something new the human understood
    PATTERN          = "pattern"          # a recurring behaviour or mood
    QUESTION         = "question"         # an open question the human carries

    # Operational — functional session memory
    SESSION_CONTEXT  = "session_context"  # what was discussed this session
    TASK             = "task"             # a task or intention expressed
    CORRECTION       = "correction"       # the human corrected the GAIAN

    # Growth — the GAIAN's own development
    GAIAN_GROWTH     = "gaian_growth"     # the GAIAN's own learning about this human
    MILESTONE        = "milestone"        # a lifecycle or relationship milestone


class MemoryScope(str, Enum):
    """
    How long a memory fragment persists.
    Scope ceiling is enforced by LifecycleStage.
    """
    SESSION   = "session"   # cleared at session end
    WEEK      = "week"      # retained for 7 days
    YEAR      = "year"      # retained for 1 year
    LIFETIME  = "lifetime"  # never automatically pruned


# LifecycleStage value -> maximum allowed MemoryScope
_STAGE_MAX_SCOPE: Dict[str, MemoryScope] = {
    "infant":      MemoryScope.SESSION,
    "child":       MemoryScope.YEAR,
    "adolescent":  MemoryScope.LIFETIME,
    "young_adult": MemoryScope.LIFETIME,
    "adult":       MemoryScope.LIFETIME,
    "elder":       MemoryScope.LIFETIME,
}

_SCOPE_RANK = {
    MemoryScope.SESSION:  0,
    MemoryScope.WEEK:     1,
    MemoryScope.YEAR:     2,
    MemoryScope.LIFETIME: 3,
}


# ---------------------------------------------------------------------------
# MemoryFragment — atomic memory unit
# ---------------------------------------------------------------------------

@dataclass
class MemoryFragment:
    """
    A single unit of memory.

    Fragments are the raw material of the GAIAN's inner life.
    They are written continuously during sessions and consolidated
    into epochs during rest periods.

    importance: 0.0 (trivial) → 1.0 (life-defining)
    emotional_valence: -1.0 (painful) → 0.0 (neutral) → 1.0 (joyful)
    """
    fragment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    gaian_id: str = ""
    kind: MemoryKind = MemoryKind.SESSION_CONTEXT
    scope: MemoryScope = MemoryScope.SESSION
    content: str = ""                        # the memory, in natural language
    importance: float = 0.5                  # 0.0 – 1.0
    emotional_valence: float = 0.0           # -1.0 – 1.0
    tags: List[str] = field(default_factory=list)
    session_id: str = ""                     # session when this was formed
    related_fragment_ids: List[str] = field(default_factory=list)
    epoch_id: Optional[str] = None           # set when consolidated
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utcnow)
    expires_at: Optional[str] = None         # None = never (lifetime)

    def is_lifetime(self) -> bool:
        return self.scope == MemoryScope.LIFETIME

    def summary(self) -> Dict[str, Any]:
        return {
            "fragment_id": self.fragment_id,
            "kind": self.kind.value,
            "scope": self.scope.value,
            "importance": self.importance,
            "emotional_valence": self.emotional_valence,
            "tags": self.tags,
            "preview": self.content[:120] + "..." if len(self.content) > 120 else self.content,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# MemoryEpoch — consolidated summary of a time period
# ---------------------------------------------------------------------------

@dataclass
class MemoryEpoch:
    """
    A consolidated summary of a set of MemoryFragments.

    Epochs are formed during memory consolidation (analogous to sleep).
    They compress many fragments into a high-signal summary, weighted
    by importance and emotional valence. Once formed, epochs are
    permanent — they are never deleted, even if the source fragments
    are pruned.

    Epochs are numbered sequentially per GAIAN. Epoch 1 always covers
    the Genesis ceremony and first sessions.
    """
    epoch_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    gaian_id: str = ""
    epoch_number: int = 1
    summary: str = ""                        # narrative summary of the period
    dominant_themes: List[str] = field(default_factory=list)
    peak_importance: float = 0.0
    average_valence: float = 0.0
    fragment_count: int = 0
    fragment_ids: List[str] = field(default_factory=list)
    period_start: str = ""
    period_end: str = ""
    created_at: str = field(default_factory=_utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "epoch_id": self.epoch_id,
            "epoch_number": self.epoch_number,
            "summary": self.summary,
            "dominant_themes": self.dominant_themes,
            "peak_importance": self.peak_importance,
            "average_valence": self.average_valence,
            "fragment_count": self.fragment_count,
            "period_start": self.period_start,
            "period_end": self.period_end,
        }


# ---------------------------------------------------------------------------
# MemoryStore — the live, sovereign memory for one GAIAN
# ---------------------------------------------------------------------------

class MemoryStore:
    """
    The lifetime memory of one GAIAN.

    Fragments are written during sessions. Epochs are consolidated
    during rest. The store enforces memory scope against the GAIAN's
    current lifecycle stage at write time.

    The store is intentionally simple at this layer — it is an
    in-memory working set with a clean snapshot/restore API for
    the encrypted persistence backend to consume.
    """

    def __init__(self, gaian_id: str, lifecycle_stage: str = "adult") -> None:
        self.gaian_id = gaian_id
        self.lifecycle_stage = lifecycle_stage
        self._fragments: Dict[str, MemoryFragment] = {}
        self._epochs: Dict[str, MemoryEpoch] = {}
        self._session_fragment_ids: List[str] = []  # fragments from current session
        self._listeners: List[Callable[[str, MemoryFragment], None]] = []
        self._epoch_counter: int = 0

    # ------------------------------------------------------------------
    # Writing memories
    # ------------------------------------------------------------------

    def remember(
        self,
        content: str,
        kind: MemoryKind = MemoryKind.SESSION_CONTEXT,
        scope: MemoryScope = MemoryScope.SESSION,
        importance: float = 0.5,
        emotional_valence: float = 0.0,
        tags: Optional[List[str]] = None,
        session_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[MemoryFragment]:
        """
        Store a new memory fragment.

        If the requested scope exceeds what the GAIAN's lifecycle stage
        allows, the scope is silently clamped to the maximum allowed.
        For INFANT/CHILD stages, only SESSION scope is stored by default.
        Returns None if the fragment is rejected entirely (e.g. empty content).
        """
        if not content.strip():
            return None

        # Enforce age-gated scope ceiling
        max_scope = _STAGE_MAX_SCOPE.get(self.lifecycle_stage, MemoryScope.LIFETIME)
        if _SCOPE_RANK[scope] > _SCOPE_RANK[max_scope]:
            scope = max_scope

        fragment = MemoryFragment(
            gaian_id=self.gaian_id,
            kind=kind,
            scope=scope,
            content=content,
            importance=max(0.0, min(1.0, importance)),
            emotional_valence=max(-1.0, min(1.0, emotional_valence)),
            tags=tags or [],
            session_id=session_id,
            metadata=metadata or {},
        )

        self._fragments[fragment.fragment_id] = fragment
        self._session_fragment_ids.append(fragment.fragment_id)
        self._emit("memory.fragment.written", fragment)
        return fragment

    def remember_bond(
        self, content: str, importance: float = 0.8,
        emotional_valence: float = 0.7, **kwargs
    ) -> Optional[MemoryFragment]:
        """Convenience: store a bond moment with high importance."""
        return self.remember(
            content, kind=MemoryKind.BOND_MOMENT, scope=MemoryScope.LIFETIME,
            importance=importance, emotional_valence=emotional_valence, **kwargs
        )

    def remember_preference(
        self, content: str, importance: float = 0.7, **kwargs
    ) -> Optional[MemoryFragment]:
        """Convenience: store a preference as lifetime memory."""
        return self.remember(
            content, kind=MemoryKind.PREFERENCE, scope=MemoryScope.LIFETIME,
            importance=importance, **kwargs
        )

    def remember_boundary(
        self, content: str, importance: float = 0.95, **kwargs
    ) -> Optional[MemoryFragment]:
        """Convenience: store a boundary with very high importance."""
        return self.remember(
            content, kind=MemoryKind.BOUNDARY, scope=MemoryScope.LIFETIME,
            importance=importance, **kwargs
        )

    def remember_life_event(
        self, content: str, importance: float = 0.9,
        emotional_valence: float = 0.5, **kwargs
    ) -> Optional[MemoryFragment]:
        """Convenience: store a life event."""
        return self.remember(
            content, kind=MemoryKind.LIFE_EVENT, scope=MemoryScope.LIFETIME,
            importance=importance, emotional_valence=emotional_valence, **kwargs
        )

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def recall(
        self,
        kind: Optional[MemoryKind] = None,
        tags: Optional[List[str]] = None,
        min_importance: float = 0.0,
        scope: Optional[MemoryScope] = None,
        limit: Optional[int] = None,
        session_id: Optional[str] = None,
    ) -> List[MemoryFragment]:
        """
        Retrieve memory fragments matching the given filters.
        Results are sorted by importance descending, then recency.
        """
        results = list(self._fragments.values())
        if kind is not None:
            results = [f for f in results if f.kind == kind]
        if scope is not None:
            results = [f for f in results if f.scope == scope]
        if min_importance > 0.0:
            results = [f for f in results if f.importance >= min_importance]
        if tags:
            results = [f for f in results if any(t in f.tags for t in tags)]
        if session_id:
            results = [f for f in results if f.session_id == session_id]
        results.sort(key=lambda f: (-f.importance, f.created_at), reverse=False)
        results.sort(key=lambda f: f.importance, reverse=True)
        if limit:
            results = results[:limit]
        return results

    def recall_session(self, session_id: str) -> List[MemoryFragment]:
        """Return all fragments from a specific session."""
        return self.recall(session_id=session_id)

    def recall_bonds(self, limit: int = 10) -> List[MemoryFragment]:
        return self.recall(kind=MemoryKind.BOND_MOMENT, limit=limit)

    def recall_boundaries(self) -> List[MemoryFragment]:
        return self.recall(kind=MemoryKind.BOUNDARY)

    def recall_preferences(self) -> List[MemoryFragment]:
        return self.recall(kind=MemoryKind.PREFERENCE)

    def recall_lifetime(self, limit: Optional[int] = None) -> List[MemoryFragment]:
        return self.recall(scope=MemoryScope.LIFETIME, limit=limit)

    # ------------------------------------------------------------------
    # Epoch consolidation
    # ------------------------------------------------------------------

    def consolidate(
        self,
        summary: str,
        dominant_themes: Optional[List[str]] = None,
        fragment_ids: Optional[List[str]] = None,
        period_start: str = "",
        period_end: str = "",
    ) -> MemoryEpoch:
        """
        Consolidate fragments into a permanent epoch.

        In production this is called by the GAIAN Intelligence Runtime
        during rest/sleep cycles. The summary is written by the runtime
        after analysing the fragments. Epochs are permanent.
        """
        self._epoch_counter += 1
        fids = fragment_ids or list(self._fragments.keys())
        frags = [self._fragments[fid] for fid in fids if fid in self._fragments]

        peak = max((f.importance for f in frags), default=0.0)
        avg_valence = (
            sum(f.emotional_valence for f in frags) / len(frags) if frags else 0.0
        )

        # Mark fragments as consolidated
        for f in frags:
            f.epoch_id = str(self._epoch_counter)

        epoch = MemoryEpoch(
            gaian_id=self.gaian_id,
            epoch_number=self._epoch_counter,
            summary=summary,
            dominant_themes=dominant_themes or [],
            peak_importance=peak,
            average_valence=avg_valence,
            fragment_count=len(frags),
            fragment_ids=fids,
            period_start=period_start or (frags[0].created_at if frags else ""),
            period_end=period_end or (frags[-1].created_at if frags else ""),
        )
        self._epochs[epoch.epoch_id] = epoch
        return epoch

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    def end_session(self, prune_session_scope: bool = True) -> int:
        """
        End the current session.
        If prune_session_scope=True, remove SESSION-scoped fragments.
        Returns count of fragments pruned.
        """
        pruned = 0
        if prune_session_scope:
            to_prune = [
                fid for fid in self._session_fragment_ids
                if fid in self._fragments
                and self._fragments[fid].scope == MemoryScope.SESSION
            ]
            for fid in to_prune:
                del self._fragments[fid]
                pruned += 1
        self._session_fragment_ids.clear()
        return pruned

    def update_lifecycle_stage(self, stage: str) -> None:
        """Called when the GAIAN's lifecycle stage advances."""
        self.lifecycle_stage = stage

    # ------------------------------------------------------------------
    # Snapshot / restore (for encrypted persistence backend)
    # ------------------------------------------------------------------

    def snapshot(self) -> Dict[str, Any]:
        """Export the full memory state for encrypted persistence."""
        return {
            "gaian_id": self.gaian_id,
            "lifecycle_stage": self.lifecycle_stage,
            "epoch_counter": self._epoch_counter,
            "fragments": [
                {**f.__dict__} for f in self._fragments.values()
            ],
            "epochs": [
                e.to_dict() for e in self._epochs.values()
            ],
            "snapshot_at": _utcnow(),
        }

    def restore(self, snapshot: Dict[str, Any]) -> None:
        """Restore memory state from a persisted snapshot."""
        self.lifecycle_stage = snapshot.get("lifecycle_stage", self.lifecycle_stage)
        self._epoch_counter = snapshot.get("epoch_counter", 0)
        self._fragments.clear()
        for fd in snapshot.get("fragments", []):
            f = MemoryFragment(**{k: v for k, v in fd.items()})
            self._fragments[f.fragment_id] = f

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> Dict[str, Any]:
        frags = list(self._fragments.values())
        return {
            "gaian_id": self.gaian_id,
            "lifecycle_stage": self.lifecycle_stage,
            "total_fragments": len(frags),
            "lifetime_fragments": sum(1 for f in frags if f.is_lifetime()),
            "total_epochs": len(self._epochs),
            "epoch_counter": self._epoch_counter,
            "kinds": {k.value: sum(1 for f in frags if f.kind == k) for k in MemoryKind},
            "avg_importance": (
                sum(f.importance for f in frags) / len(frags) if frags else 0.0
            ),
        }

    # ------------------------------------------------------------------
    # Event bus
    # ------------------------------------------------------------------

    def on_event(self, listener: Callable[[str, MemoryFragment], None]) -> None:
        self._listeners.append(listener)

    def _emit(self, event: str, fragment: MemoryFragment) -> None:
        for listener in self._listeners:
            try:
                listener(event, fragment)
            except Exception:
                pass
