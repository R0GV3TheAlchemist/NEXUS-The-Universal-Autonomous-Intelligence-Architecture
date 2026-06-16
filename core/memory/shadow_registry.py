"""Shadow Registry — Canon C23: Failure Mode Catalogue & Shadow Pattern Tracking.

The Shadow Registry is GAIA's autopoietic learning mechanism.
It logs failure modes, aversions, shadow patterns, and containment events
for pattern learning — NOT for judgment.

C23 principle: the Shadow Registry exists so GAIA can understand
what states a human moves into, what triggered them, and what helped.
Privacy: shadow logs are NEVER surfaced to the user without explicit request.

The Shadow Registry integrates with the Audit Trail (C03) and the
Gaian Twin Profile (C04) to provide a complete picture of the
relationship over time.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class ShadowPattern(str, Enum):
    """Known shadow patterns tracked by the registry.

    These are patterns, not diagnoses. They describe recurring
    dynamics in the HP-Gaian relationship.
    """
    AVOIDANCE = "AVOIDANCE"               # Consistently sidestepping a topic
    PROJECTION = "PROJECTION"             # Attributing internal state to external cause
    CYCLING = "CYCLING"                   # Returning to the same unresolved loop
    INFLATION = "INFLATION"               # Grandiosity, bypassing integration
    DEFLATION = "DEFLATION"               # Minimising, self-deprecation as avoidance
    CONTAINMENT_BREACH = "CONTAINMENT_BREACH"  # GAIA moved too fast for the HP
    PREMATURE_RESOLUTION = "PREMATURE_RESOLUTION"  # GAIA resolved before HP was ready
    PATTERN_FORCING = "PATTERN_FORCING"   # GAIA made false connections (Light Cone violation)
    MISATTUNEMENT = "MISATTUNEMENT"       # GAIA read the HP's state incorrectly
    MORAL_FILTER_CATCH = "MORAL_FILTER_CATCH"  # Response caught by Golden Compass


@dataclass
class ShadowEntry:
    """A single shadow registry entry — the atomic unit of shadow pattern tracking."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    gaian_id: str = ""
    human_principal_id: str = ""
    session_id: str = ""
    pattern: ShadowPattern = ShadowPattern.AVOIDANCE
    description: str = ""                  # What happened
    trigger: Optional[str] = None          # What appeared to trigger it
    what_helped: Optional[str] = None      # What intervention (if any) helped
    is_resolved: bool = False
    resolved_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = field(default_factory=dict)

    def resolve(self, what_helped: Optional[str] = None) -> None:
        self.is_resolved = True
        self.resolved_at = datetime.now(timezone.utc)
        if what_helped:
            self.what_helped = what_helped

    def __repr__(self) -> str:
        return (
            f"<ShadowEntry {self.id[:8]} pattern={self.pattern.value} "
            f"resolved={self.is_resolved}>"
        )


class ShadowRegistry:
    """C23: The failure mode catalogue and shadow pattern tracker.

    Never surfaced to the user without explicit request.
    Used by GAIA for autopoietic learning — understanding the relationship
    over time to be a better companion.
    """

    def __init__(self, gaian_id: str, human_principal_id: str) -> None:
        self.gaian_id = gaian_id
        self.human_principal_id = human_principal_id
        self._entries: dict[str, ShadowEntry] = {}
        self._session_index: dict[str, list[str]] = {}

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def log(
        self,
        pattern: ShadowPattern,
        session_id: str,
        description: str,
        trigger: Optional[str] = None,
    ) -> ShadowEntry:
        """Log a new shadow pattern event."""
        entry = ShadowEntry(
            gaian_id=self.gaian_id,
            human_principal_id=self.human_principal_id,
            session_id=session_id,
            pattern=pattern,
            description=description,
            trigger=trigger,
        )
        self._entries[entry.id] = entry
        self._session_index.setdefault(session_id, []).append(entry.id)
        return entry

    def resolve_entry(self, entry_id: str, what_helped: Optional[str] = None) -> bool:
        entry = self._entries.get(entry_id)
        if not entry:
            return False
        entry.resolve(what_helped)
        return True

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def all(self, unresolved_only: bool = False) -> list[ShadowEntry]:
        entries = list(self._entries.values())
        if unresolved_only:
            entries = [e for e in entries if not e.is_resolved]
        return sorted(entries, key=lambda e: e.created_at)

    def by_pattern(self, pattern: ShadowPattern) -> list[ShadowEntry]:
        return [e for e in self.all() if e.pattern == pattern]

    def by_session(self, session_id: str) -> list[ShadowEntry]:
        ids = self._session_index.get(session_id, [])
        return [self._entries[eid] for eid in ids if eid in self._entries]

    def active_flags(self) -> list[ShadowPattern]:
        """Return patterns with unresolved entries — for Gaian Twin Profile flags."""
        patterns = {e.pattern for e in self.all(unresolved_only=True)}
        return list(patterns)

    def count(self, unresolved_only: bool = False) -> int:
        return len(self.all(unresolved_only))

    def pattern_frequency(self) -> dict[str, int]:
        """Return a frequency map of all logged patterns."""
        freq: dict[str, int] = {}
        for entry in self.all():
            key = entry.pattern.value
            freq[key] = freq.get(key, 0) + 1
        return dict(sorted(freq.items(), key=lambda x: -x[1]))

    def __repr__(self) -> str:
        return (
            f"<ShadowRegistry gaian={self.gaian_id[:8]} "
            f"total={self.count()} unresolved={self.count(unresolved_only=True)}>"
        )
