"""
shadow_engine/integration.py
Integration Tracker — monitors shadow integration progress over time.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional

# ---------------------------------------------------------------------------
# Module-level constants (all imported by tests)
# ---------------------------------------------------------------------------

JOURNAL_ENTRY_GAIN:   float = 0.02   # per journal entry
JOURNAL_DAILY_CAP:    float = 0.10   # max journal gain per day
STAGE_ADVANCE_GAIN:   float = 0.15   # awarded on shadow stage advance
REFLECTION_GAIN:      float = 0.05   # per reflection session
PASSIVE_GAIN_PER_DAY: float = 0.01   # passive gain when low intensity ≥7 days
DECAY_PER_DAY:        float = 0.005  # daily decay when no journaling


# ---------------------------------------------------------------------------
# State dataclass (held by tracker)
# ---------------------------------------------------------------------------

@dataclass
class _TrackerState:
    user_id:             str
    archetype:           str
    progress:            float = 0.0      # 0.0 – 1.0
    journal_gain_today:  float = 0.0
    last_journal_date:   Optional[date] = None
    low_intensity_days:  int = 0


# ---------------------------------------------------------------------------
# IntegrationTracker
# ---------------------------------------------------------------------------

class IntegrationTracker:
    """
    Tracks per-user shadow integration progress.

    All gain / decay constants are module-level so tests can import them.
    """

    def __init__(self, state: _TrackerState) -> None:
        self._s = state

    # ------------------------------------------------------------------ #
    #  Factory                                                             #
    # ------------------------------------------------------------------ #

    @classmethod
    def new(cls, user_id: str, archetype: str = "Orphan") -> "IntegrationTracker":
        return cls(_TrackerState(user_id=user_id, archetype=archetype))

    # ------------------------------------------------------------------ #
    #  Properties                                                          #
    # ------------------------------------------------------------------ #

    @property
    def progress(self) -> float:
        return self._s.progress

    @property
    def user_id(self) -> str:
        return self._s.user_id

    @property
    def archetype(self) -> str:
        return self._s.archetype

    # ------------------------------------------------------------------ #
    #  Accrual methods                                                     #
    # ------------------------------------------------------------------ #

    def accrue_journal_entry(self) -> float:
        """Award JOURNAL_ENTRY_GAIN up to JOURNAL_DAILY_CAP per day."""
        today = date.today()
        # Reset daily cap on new day
        if self._s.last_journal_date != today:
            self._s.journal_gain_today = 0.0
            self._s.last_journal_date  = today

        remaining_cap = max(0.0, JOURNAL_DAILY_CAP - self._s.journal_gain_today)
        gain          = min(JOURNAL_ENTRY_GAIN, remaining_cap)
        self._s.journal_gain_today += gain
        self._s.progress = min(1.0, self._s.progress + gain)
        return gain

    def accrue_stage_advance(self) -> float:
        gain = STAGE_ADVANCE_GAIN
        self._s.progress = min(1.0, self._s.progress + gain)
        return gain

    def accrue_reflection_session(self) -> float:
        gain = REFLECTION_GAIN
        self._s.progress = min(1.0, self._s.progress + gain)
        return gain

    # ------------------------------------------------------------------ #
    #  Daily tick                                                          #
    # ------------------------------------------------------------------ #

    def tick_daily(
        self,
        shadow_intensity:         float,
        journal_entries_this_week: int,
    ) -> None:
        """Called once per calendar day to apply decay / passive gain."""
        # Reset daily journal cap
        self._s.journal_gain_today = 0.0
        self._s.last_journal_date  = None

        # Decay if no journaling this week
        if journal_entries_this_week == 0:
            self._s.progress = max(0.0, self._s.progress - DECAY_PER_DAY)

        # Passive gain counter
        if shadow_intensity <= 0.3:
            self._s.low_intensity_days += 1
        else:
            self._s.low_intensity_days = 0

        if self._s.low_intensity_days >= 7:
            self._s.progress = min(1.0, self._s.progress + PASSIVE_GAIN_PER_DAY)
            self._s.low_intensity_days = 0

    # ------------------------------------------------------------------ #
    #  Serialisation                                                       #
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        return {
            "user_id":   self._s.user_id,
            "archetype": self._s.archetype,
            "progress":  round(self._s.progress, 6),
        }
