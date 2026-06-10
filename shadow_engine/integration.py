"""
shadow_engine/integration.py
Integration Tracker — monitors shadow integration progress over time.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from shadow_engine.types import ShadowArchetype, ShadowRecord, ACTIVATION_THRESHOLD


@dataclass
class IntegrationEntry:
    archetype:       ShadowArchetype
    integration_pct: float = 0.0
    activations:     int   = 0
    integrations:    int   = 0

    def to_dict(self) -> dict:
        return {
            "archetype":       self.archetype.value,
            "integration_pct": round(self.integration_pct, 4),
            "activations":     self.activations,
            "integrations":    self.integrations,
        }


class IntegrationTracker:
    """
    Tracks per-archetype integration progress across shadow activation events.
    """

    def __init__(self) -> None:
        self._entries: Dict[ShadowArchetype, IntegrationEntry] = {}

    def _get_or_create(self, archetype: ShadowArchetype) -> IntegrationEntry:
        if archetype not in self._entries:
            self._entries[archetype] = IntegrationEntry(archetype=archetype)
        return self._entries[archetype]

    def record(self, record: ShadowRecord) -> IntegrationEntry:
        entry = self._get_or_create(record.archetype)
        if record.is_activated:
            entry.activations += 1
        if record.integrated:
            entry.integrations += 1
            pct_change = min(100.0, 100.0 * entry.integrations / max(1, entry.activations))
            entry.integration_pct = pct_change
        return entry

    def get(self, archetype: ShadowArchetype) -> Optional[IntegrationEntry]:
        return self._entries.get(archetype)

    def all_entries(self) -> List[IntegrationEntry]:
        return list(self._entries.values())

    def overall_pct(self) -> float:
        if not self._entries:
            return 0.0
        return sum(e.integration_pct for e in self._entries.values()) / len(self._entries)
