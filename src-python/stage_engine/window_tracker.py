"""
Transition Window Tracker  (Issue #63)

The StageEngine needs to know:
  - How many consecutive days the forward-transition marker set has been met
  - How many consecutive days the regression marker pattern has been present

These counts were previously caller-managed.  This module persists them
in SovereignMemory (the stage_window_state table) so the engine never
loses state across restarts.

Schema (created by SovereignMemory if not present)::

    CREATE TABLE IF NOT EXISTS stage_window_state (
        principal_id              TEXT PRIMARY KEY,
        days_forward_window_met   INTEGER NOT NULL DEFAULT 0,
        days_regression_window    INTEGER NOT NULL DEFAULT 0,
        last_evaluated_date       TEXT,           -- ISO date YYYY-MM-DD
        updated_at                INTEGER NOT NULL
    );

The tracker is date-keyed: it increments once per calendar day maximum.
Multiple evaluations on the same day are idempotent.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Optional

from .types import MarkerScores
from .transitions import check_forward_transition, check_regression


class WindowTracker:
    """
    Persists and auto-increments the two transition window counters.

    Usage::

        tracker = WindowTracker(memory)
        fwd, reg = tracker.get_and_update(
            principal_id="user123",
            scores=marker_scores,
            current_stage=2,
        )
        result = stage_engine.evaluate(
            ...,
            days_forward_window_met=fwd,
            days_regression_window=reg,
        )
    """

    CREATE_SQL = """
        CREATE TABLE IF NOT EXISTS stage_window_state (
            principal_id              TEXT PRIMARY KEY,
            days_forward_window_met   INTEGER NOT NULL DEFAULT 0,
            days_regression_window    INTEGER NOT NULL DEFAULT 0,
            last_evaluated_date       TEXT,
            updated_at                INTEGER NOT NULL
        );
    """

    def __init__(self, memory) -> None:
        self._memory = memory
        self._ensure_table()

    def _ensure_table(self) -> None:
        self._memory._conn.execute(self.CREATE_SQL)
        self._memory._conn.commit()

    def get_and_update(
        self,
        principal_id: str,
        scores: MarkerScores,
        current_stage: int,
    ) -> tuple[int, int]:
        """
        Read existing window counts, advance them if today is a new day,
        reset them if the conditions are no longer met, persist, and return.

        Returns
        -------
        (days_forward_window_met, days_regression_window)
        """
        today = datetime.now(timezone.utc).date().isoformat()
        now   = int(time.time() * 1000)
        conn  = self._memory._conn

        row = conn.execute(
            "SELECT days_forward_window_met, days_regression_window, "
            "last_evaluated_date FROM stage_window_state WHERE principal_id=?",
            (principal_id,),
        ).fetchone()

        if row:
            fwd  = row["days_forward_window_met"]
            reg  = row["days_regression_window"]
            last = row["last_evaluated_date"]
        else:
            fwd, reg, last = 0, 0, None

        is_new_day = (last != today)

        # Determine whether forward/regression conditions are met RIGHT NOW
        to_stage = current_stage + 1
        fwd_eligible = to_stage <= 5

        from .transitions import markers_met_for_transition, FORWARD_MARKERS_REQUIRED, REGRESSION_MARKERS_REQUIRED
        from .types import FORWARD_MARKERS_REQUIRED  as FMR, REGRESSION_MARKERS_REQUIRED as RMR

        met_forward = []
        if fwd_eligible:
            from .transitions import markers_met_for_transition
            met_forward = markers_met_for_transition(scores, current_stage, to_stage)

        from .transitions import check_regression
        # For regression check we use a dummy 0-day window to just get the bool
        _, regressed_markers = check_regression(scores, current_stage, days_regression_window=0)
        is_regressing = len(regressed_markers) >= RMR

        is_forwarding  = len(met_forward) >= FMR

        if is_new_day:
            fwd = (fwd + 1) if is_forwarding  else 0
            reg = (reg + 1) if is_regressing  else 0
        # same day: keep existing counts unchanged (idempotent)

        conn.execute(
            """
            INSERT INTO stage_window_state (
                principal_id, days_forward_window_met, days_regression_window,
                last_evaluated_date, updated_at
            ) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(principal_id) DO UPDATE SET
                days_forward_window_met = excluded.days_forward_window_met,
                days_regression_window  = excluded.days_regression_window,
                last_evaluated_date     = excluded.last_evaluated_date,
                updated_at              = excluded.updated_at
            """,
            (principal_id, fwd, reg, today, now),
        )
        conn.commit()
        return fwd, reg
