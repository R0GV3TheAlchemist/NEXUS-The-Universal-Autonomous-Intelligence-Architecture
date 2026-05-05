"""GAIA-OS Stage Engine — Main orchestrator

Issue #63 | Pillar I: Magnum Opus

Changelog vs. initial scaffold
------------------------------
* Added _score_only() helper so router can pre-score before WindowTracker.
* Schumann alignment is now injected via schumann_bridge.py — engine.py
  itself stays agnostic to SchumannState type.
* All other logic unchanged from the original scaffold.
"""

from __future__ import annotations

import json
import time
from typing import Sequence

from sovereign_memory import SovereignMemory
from .markers import MarkerScorer
from .transitions import check_forward_transition, check_regression
from .types import (
    MarkerScores,
    STAGE_NAMES,
    StageRecord,
    StageTransition,
    TransitionResult,
)

_MS = 1000


class StageEngine:
    """
    Orchestrates stage evaluation for a single principal.

    Typical call flow (called once per day or after a major user event):
        result = engine.evaluate(principal_id, signal_bundle)
        if result.transition:
            emit_ceremony(result.transition)

    The engine:
    1. Scores all six markers via MarkerScorer.
    2. Upserts the stage_records row in SovereignMemory.
    3. Checks forward transition and regression conditions.
    4. If a transition fires, appends a stage_transitions row.
    5. Returns a TransitionResult.
    """

    def __init__(self, memory: SovereignMemory) -> None:
        self.memory = memory

    # ─────────────────────────────────────────────
    # PRIMARY INTERFACE
    # ─────────────────────────────────────────────

    def evaluate(
        self,
        principal_id: str,
        goal_states: list[str],
        hrv_rmssd_history: list[float],
        alignment_score_history: list[float],
        journal_entries: list[dict],
        focus_session_minutes: list[float],
        goals_completed: int,
        goals_abandoned: int,
        valence_history: list[float],
        days_forward_window_met: int = 0,
        days_regression_window: int = 0,
    ) -> TransitionResult:
        """
        Score all markers, evaluate transitions, persist state.

        Args:
            principal_id:              User/Gaian identifier.
            goal_states:               Daily decision states list (last 30 days).
            hrv_rmssd_history:         HRV RMSSD readings (last 30 days).
            alignment_score_history:   Schumann alignment scores 0–100 (last 30 days).
            journal_entries:           Processed journal feature dicts (last 14 days).
            focus_session_minutes:     Focus session lengths in minutes (last 14 days).
            goals_completed:           Completed goal count (last 30 days).
            goals_abandoned:           Abandoned goal count (last 30 days).
            valence_history:           Affect valence readings (last 30 days).
            days_forward_window_met:   Days the current marker set has been at
                                       forward-transition thresholds. Use
                                       WindowTracker.get_and_update() to supply this.
            days_regression_window:    Days the regression pattern has been present.

        Returns:
            TransitionResult with updated StageRecord and optional StageTransition.
        """
        now = int(time.time() * _MS)

        scores = MarkerScorer.compute(
            goal_states=goal_states,
            hrv_rmssd_history=hrv_rmssd_history,
            alignment_score_history=alignment_score_history,
            journal_entries=journal_entries,
            focus_session_minutes=focus_session_minutes,
            goals_completed=goals_completed,
            goals_abandoned=goals_abandoned,
            valence_history=valence_history,
        )

        current_stage = self._load_current_stage(principal_id, now)
        stage_entered_at = self._load_stage_entered_at(principal_id, now)
        days_in_stage = max(0, (now - stage_entered_at) // (86_400 * _MS))

        should_forward, forward_markers = check_forward_transition(
            scores, current_stage, days_forward_window_met
        )
        should_regress, regress_markers = check_regression(
            scores, current_stage, days_regression_window
        )

        transition: StageTransition | None = None

        if should_forward and not should_regress:
            new_stage = current_stage + 1
            transition = StageTransition(
                principal_id=principal_id,
                from_stage=current_stage,
                to_stage=new_stage,
                transitioned_at=now,
                is_regression=False,
                markers_met=forward_markers,
            )
            self._persist_transition(transition)
            current_stage = new_stage
            stage_entered_at = now
            days_in_stage = 0

        elif should_regress:
            new_stage = max(1, current_stage - 1)
            transition = StageTransition(
                principal_id=principal_id,
                from_stage=current_stage,
                to_stage=new_stage,
                transitioned_at=now,
                is_regression=True,
                markers_met=regress_markers,
            )
            self._persist_transition(transition)
            current_stage = new_stage
            stage_entered_at = now
            days_in_stage = 0

        record = StageRecord(
            principal_id=principal_id,
            current_stage=current_stage,
            stage_name=STAGE_NAMES[current_stage],
            stage_entered_at=stage_entered_at,
            days_in_stage=days_in_stage,
            marker_scores=scores,
            transition_candidate=should_forward and not should_regress,
            regression_risk=should_regress,
            updated_at=now,
        )
        self._upsert_stage_record(record)
        return TransitionResult(record=record, transition=transition)

    def _score_only(
        self,
        goal_states: list[str],
        hrv_rmssd_history: list[float],
        alignment_score_history: list[float],
        journal_entries: list[dict],
        focus_session_minutes: list[float],
        goals_completed: int,
        goals_abandoned: int,
        valence_history: list[float],
    ) -> MarkerScores:
        """Run scoring only, no persistence.  Used by router + WindowTracker."""
        return MarkerScorer.compute(
            goal_states=goal_states,
            hrv_rmssd_history=hrv_rmssd_history,
            alignment_score_history=alignment_score_history,
            journal_entries=journal_entries,
            focus_session_minutes=focus_session_minutes,
            goals_completed=goals_completed,
            goals_abandoned=goals_abandoned,
            valence_history=valence_history,
        )

    def get_stage_history(self, principal_id: str) -> list:
        return self.memory.get_stage_history(principal_id)

    # ─────────────────────────────────────────────
    # INTERNAL HELPERS
    # ─────────────────────────────────────────────

    def _load_current_stage(self, principal_id: str, now: int) -> int:
        conn = self.memory._conn
        row = conn.execute(
            "SELECT current_stage FROM stage_records WHERE principal_id=?",
            (principal_id,),
        ).fetchone()
        return row["current_stage"] if row else 1

    def _load_stage_entered_at(self, principal_id: str, now: int) -> int:
        conn = self.memory._conn
        row = conn.execute(
            "SELECT stage_entered_at FROM stage_records WHERE principal_id=?",
            (principal_id,),
        ).fetchone()
        return row["stage_entered_at"] if row else now

    def _upsert_stage_record(self, record: StageRecord) -> None:
        conn = self.memory._conn
        scores = record.marker_scores
        conn.execute(
            """
            INSERT INTO stage_records (
                principal_id, current_stage, stage_entered_at, days_in_stage,
                decision_entropy, hrv_coherence, journaling_depth,
                focus_session_length_min, goal_completion_rate,
                emotional_arc_stability, transition_candidate,
                regression_risk, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(principal_id) DO UPDATE SET
                current_stage = excluded.current_stage,
                stage_entered_at = excluded.stage_entered_at,
                days_in_stage = excluded.days_in_stage,
                decision_entropy = excluded.decision_entropy,
                hrv_coherence = excluded.hrv_coherence,
                journaling_depth = excluded.journaling_depth,
                focus_session_length_min = excluded.focus_session_length_min,
                goal_completion_rate = excluded.goal_completion_rate,
                emotional_arc_stability = excluded.emotional_arc_stability,
                transition_candidate = excluded.transition_candidate,
                regression_risk = excluded.regression_risk,
                updated_at = excluded.updated_at
            """,
            (
                record.principal_id,
                record.current_stage,
                record.stage_entered_at,
                record.days_in_stage,
                scores.decision_entropy,
                scores.hrv_coherence,
                scores.journaling_depth,
                scores.focus_session_length_min,
                scores.goal_completion_rate,
                scores.emotional_arc_stability,
                int(record.transition_candidate),
                int(record.regression_risk),
                record.updated_at,
            ),
        )
        conn.commit()

    def _persist_transition(self, t: StageTransition) -> None:
        conn = self.memory._conn
        conn.execute(
            """
            INSERT INTO stage_transitions (
                principal_id, from_stage, to_stage, transitioned_at,
                is_regression, markers_met_json, ceremony_shown
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                t.principal_id,
                t.from_stage,
                t.to_stage,
                t.transitioned_at,
                int(t.is_regression),
                json.dumps(t.markers_met),
                int(t.ceremony_shown),
            ),
        )
        conn.commit()
