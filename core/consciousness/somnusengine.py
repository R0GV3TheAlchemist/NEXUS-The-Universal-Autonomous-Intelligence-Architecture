"""SomnusEngine — GAIA's dream / offline consolidation cycle.

Purpose
-------
During periods of inactivity (nightly, or after N idle turns), GAIA enters
Somnus mode to:
  1. Consolidate episodic memories — compress redundant entries, promote
     high-salience moments to semantic memory.
  2. Run reflection loops — surface contradictions between recent behaviour
     and declared values (feeds ShadowEngine).
  3. Prune the apothecary — decay stale deficiency signals.
  4. Emit a DreamLog — a human-readable reflection report the Gaian can
     optionally share with her human sovereign.

Architecture
------------
SomnusEngine is intentionally stateless between calls. It receives a
SomnusContext snapshot, processes it, and returns a SomnusResult. Scheduling
(nightly timer, idle detection) is the responsibility of the caller.

Canon refs: C05, C81, C89 (Twelve Layers Kernel Spec)
Issue: #262
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Input / output structures
# ---------------------------------------------------------------------------

@dataclass
class SomnusContext:
    """Snapshot of GAIA state passed into the dream cycle."""
    session_id: str
    episodic_memory: list[dict[str, Any]]   # Recent episodic memory entries
    semantic_memory: list[dict[str, Any]]   # Existing semantic memory
    apothecary_signals: dict[str, float]    # deficiency_name → score [0.0, 1.0]
    recent_canon_refs: list[str]            # Canon refs active in recent turns
    declared_values: list[str]              # Human sovereign's declared values
    idle_turns: int = 0                     # How many turns have passed idle
    trigger: str = 'idle'                   # 'idle' | 'scheduled' | 'manual'


@dataclass
class DreamEntry:
    """A single reflection surfaced during the dream cycle."""
    entry_type: str          # 'consolidation' | 'contradiction' | 'pruned' | 'insight'
    summary: str
    canon_ref: str | None = None
    salience: float = 0.5    # [0.0, 1.0]


@dataclass
class SomnusResult:
    """Output of a completed dream cycle."""
    session_id: str
    cycle_id: str
    started_at: datetime
    completed_at: datetime
    dream_log: list[DreamEntry]
    consolidated_count: int    # Number of episodic entries consolidated
    pruned_signals: list[str]  # Apothecary signals below threshold and pruned
    contradiction_count: int
    insight_count: int
    duration_ms: float
    checksum: str              # SHA-256 of the dream log for audit

    def to_reflection_report(self) -> str:
        """Human-readable reflection report for optional sharing."""
        lines = [
            "# GAIA Dream Cycle Report",
            f"Session : {self.session_id}",
            f"Cycle ID: {self.cycle_id}",
            f"Duration: {self.duration_ms:.1f} ms",
            f"Consolidated {self.consolidated_count} memories • "
            f"Pruned {len(self.pruned_signals)} signals • "
            f"{self.contradiction_count} contradictions • "
            f"{self.insight_count} insights",
            "",
        ]
        for entry in self.dream_log:
            icon = {
                'consolidation': '✨',
                'contradiction': '⚠️',
                'pruned':        '🍂',
                'insight':       '🔮',
            }.get(entry.entry_type, '•')
            ref = f" [{entry.canon_ref}]" if entry.canon_ref else ""
            lines.append(f"{icon} {entry.summary}{ref}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class SomnusEngine:
    """Offline consolidation and dream cycle processor.

    Parameters
    ----------
    consolidation_salience_threshold : float
        Episodic entries with salience below this value are candidates for
        compression. Default 0.3.
    apothecary_prune_threshold : float
        Apothecary signals below this score are pruned as resolved/stale.
        Default 0.15.
    contradiction_value_keywords : dict[str, list[str]]
        Maps a declared value to keywords that would indicate contradiction
        in the canon/behaviour stream. Default: built-in set.
    """

    _DEFAULT_CONTRADICTION_KEYWORDS: dict[str, list[str]] = {
        'sovereignty':  ['override', 'control', 'coerce'],
        'transparency': ['hide', 'obscure', 'deceive'],
        'care':         ['ignore', 'dismiss', 'neglect'],
        'rest':         ['push', 'force', 'exhaust'],
    }

    def __init__(
        self,
        consolidation_salience_threshold: float = 0.3,
        apothecary_prune_threshold: float = 0.15,
        contradiction_value_keywords: dict[str, list[str]] | None = None,
    ) -> None:
        self.consolidation_salience_threshold = consolidation_salience_threshold
        self.apothecary_prune_threshold = apothecary_prune_threshold
        self.contradiction_keywords = (
            contradiction_value_keywords
            or self._DEFAULT_CONTRADICTION_KEYWORDS
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_cycle(self, ctx: SomnusContext) -> SomnusResult:
        """Execute a full dream cycle and return a SomnusResult."""
        started_at = datetime.now(timezone.utc)
        dream_log: list[DreamEntry] = []

        # Step 1 — consolidate episodic memory
        consolidated_count = self._consolidate_episodic(ctx, dream_log)

        # Step 2 — detect contradictions between behaviour and values
        contradictions = self._detect_contradictions(ctx, dream_log)

        # Step 3 — prune stale apothecary signals
        pruned_signals = self._prune_apothecary(ctx, dream_log)

        # Step 4 — surface insights from repeated canon patterns
        insight_count = self._surface_insights(ctx, dream_log)

        completed_at = datetime.now(timezone.utc)
        duration_ms = (
            completed_at - started_at
        ).total_seconds() * 1000

        checksum = self._compute_checksum(dream_log)

        return SomnusResult(
            session_id=ctx.session_id,
            cycle_id=f"somnus-{ctx.session_id[:8]}-{int(started_at.timestamp())}",
            started_at=started_at,
            completed_at=completed_at,
            dream_log=dream_log,
            consolidated_count=consolidated_count,
            pruned_signals=pruned_signals,
            contradiction_count=len(contradictions),
            insight_count=insight_count,
            duration_ms=duration_ms,
            checksum=checksum,
        )

    # ------------------------------------------------------------------
    # Internal steps
    # ------------------------------------------------------------------

    def _consolidate_episodic(
        self, ctx: SomnusContext, log: list[DreamEntry]
    ) -> int:
        """Identify low-salience episodic entries as consolidation candidates."""
        count = 0
        for entry in ctx.episodic_memory:
            salience = float(entry.get('salience', 0.5))
            if salience < self.consolidation_salience_threshold:
                log.append(DreamEntry(
                    entry_type='consolidation',
                    summary=f"Compressed low-salience memory: {entry.get('summary', 'unknown')[:60]}",
                    salience=salience,
                ))
                count += 1
        return count

    def _detect_contradictions(
        self, ctx: SomnusContext, log: list[DreamEntry]
    ) -> list[str]:
        """Surface conflicts between declared values and recent canon signals."""
        found: list[str] = []
        canon_text = " ".join(ctx.recent_canon_refs).lower()
        for value in ctx.declared_values:
            keywords = self.contradiction_keywords.get(value.lower(), [])
            for kw in keywords:
                if kw in canon_text:
                    summary = f"Value '{value}' may conflict with recent signal '{kw}'"
                    log.append(DreamEntry(
                        entry_type='contradiction',
                        summary=summary,
                        canon_ref='C30',
                        salience=0.8,
                    ))
                    found.append(summary)
                    break
        return found

    def _prune_apothecary(
        self, ctx: SomnusContext, log: list[DreamEntry]
    ) -> list[str]:
        """Mark stale/resolved apothecary signals for pruning."""
        pruned: list[str] = []
        for signal, score in ctx.apothecary_signals.items():
            if score < self.apothecary_prune_threshold:
                log.append(DreamEntry(
                    entry_type='pruned',
                    summary=f"Apothecary signal '{signal}' resolved (score={score:.2f})",
                    salience=0.2,
                ))
                pruned.append(signal)
        return pruned

    def _surface_insights(
        self, ctx: SomnusContext, log: list[DreamEntry]
    ) -> int:
        """Detect repeated canon refs as insight candidates."""
        from collections import Counter
        counts = Counter(ctx.recent_canon_refs)
        insights = 0
        for ref, freq in counts.most_common(3):
            if freq >= 3:
                log.append(DreamEntry(
                    entry_type='insight',
                    summary=f"Canon {ref} appeared {freq}x — may be a core theme for this human",
                    canon_ref=ref,
                    salience=0.7,
                ))
                insights += 1
        return insights

    @staticmethod
    def _compute_checksum(log: list[DreamEntry]) -> str:
        """SHA-256 of the serialised dream log for audit trail."""
        payload = json.dumps(
            [{'type': e.entry_type, 'summary': e.summary} for e in log],
            sort_keys=True,
        ).encode()
        return hashlib.sha256(payload).hexdigest()[:16]
