"""
GAIA-OS Stage Engine
Pillar: Magnum Opus (Pillar I)
Spec: docs/knowledge/STAGE_ENGINE_SPEC.md

Tracks each user's position along the five-stage developmental arc.
Evaluates behavioral, biometric, and cognitive signals to determine
stage, trigger transitions, and gate downstream system behavior.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

StageNumber = Literal[1, 2, 3, 4, 5]

# Minimum days a user must sustain transition markers before advancing
MIN_TRANSITION_WINDOW_DAYS: dict[tuple[int, int], int] = {
    (1, 2): 21,
    (2, 3): 30,
    (3, 4): 45,
    (4, 5): 60,
}

# Markers required to advance (4 of 6)
ADVANCE_MARKER_THRESHOLD = 4

# Markers required for regression (5 of 6 prior-stage markers for 14+ days)
REGRESSION_MARKER_THRESHOLD = 5
REGRESSION_WINDOW_DAYS = 14

# Shadow Engine mode by stage
_SHADOW_MODE_MAP: dict[int, str] = {
    1: "off",
    2: "observation",
    3: "full",
    4: "synthesis",
    5: "collective",
}


# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class MarkerScores:
    """Six behavioral/biometric dimensions, each normalized 0–100."""
    decision_entropy: float        # 0-100 (higher = more chaotic)
    hrv_coherence: float           # 0-100 (higher = more coherent)
    journaling_depth: float        # 0-100
    focus_session_length: float    # minutes avg
    goal_completion_rate: float    # 0-100
    emotional_arc_stability: float # 0-100


@dataclass
class StageTransition:
    from_stage: int
    to_stage: int
    transitioned_at: str           # ISO 8601
    markers_met: list[str]
    ceremony_shown: bool = False
    label: str = ""               # e.g. "3R" for regression, "" for advance


@dataclass
class StageRecord:
    user_id: str
    current_stage: int             # 1–5
    stage_entered_at: str          # ISO 8601
    days_in_stage: int
    marker_scores: MarkerScores
    transition_candidate: bool = False
    regression_risk: bool = False
    stage_history: list[StageTransition] = field(default_factory=list)


# ---------------------------------------------------------------------------
# MarkerScorer
# ---------------------------------------------------------------------------

class MarkerScorer:
    """
    Normalizes raw behavioral/biometric inputs into MarkerScores.

    Stage advance / regression logic works on the *normalized* scores,
    not the raw sensor values. Each dimension is clamped to [0, 100].
    """

    @staticmethod
    def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
        return max(lo, min(hi, value))

    def score(
        self,
        *,
        decision_entropy_raw: float,      # 0-100, higher = more chaotic
        hrv_rmssd_ms: float,              # raw HRV RMSSD in ms (20–100 typical)
        journal_word_count: float,        # words per session
        focus_minutes_avg: float,         # minutes per session
        goal_completion_pct: float,       # 0–100
        emotional_volatility_raw: float,  # 0–100, higher = more volatile
    ) -> MarkerScores:
        """
        Map raw sensor / behavioral values to 0–100 normalized scores.

        HRV: normalizes RMSSD against a 20–100 ms baseline range.
        Journaling: 500+ words = score 100.
        Emotional arc stability: inverse of volatility.
        """
        hrv_coherence = self._clamp((hrv_rmssd_ms - 20.0) / 80.0 * 100.0)
        journaling_depth = self._clamp(journal_word_count / 500.0 * 100.0)
        emotional_arc_stability = self._clamp(100.0 - emotional_volatility_raw)

        return MarkerScores(
            decision_entropy=self._clamp(decision_entropy_raw),
            hrv_coherence=hrv_coherence,
            journaling_depth=journaling_depth,
            focus_session_length=self._clamp(focus_minutes_avg, 0, 240),
            goal_completion_rate=self._clamp(goal_completion_pct),
            emotional_arc_stability=emotional_arc_stability,
        )


# ---------------------------------------------------------------------------
# Stage Marker Thresholds
# ---------------------------------------------------------------------------

# For each stage, defines the ADVANCE markers (signals that the user is ready
# to move to the NEXT stage).  A marker is "met" if the score crosses its
# threshold in the correct direction.
#
# Format: (dimension, operator, threshold)
# operator: 'lt' (below threshold = marker met), 'gte' (at/above = met)

ADVANCE_MARKERS: dict[int, list[tuple[str, str, float]]] = {
    # Stage 1 → 2: journaling increasing, HRV improving, focus lengthening
    1: [
        ("decision_entropy",        "lt",  70.0),   # chaos reducing
        ("hrv_coherence",           "gte", 30.0),   # HRV improving
        ("journaling_depth",        "gte", 20.0),   # journaling appearing
        ("focus_session_length",    "gte", 15.0),   # 15+ min sessions
        ("goal_completion_rate",    "gte", 20.0),   # 20%+ completion
        ("emotional_arc_stability", "gte", 30.0),   # volatility reducing
    ],
    # Stage 2 → 3
    2: [
        ("decision_entropy",        "lt",  60.0),
        ("hrv_coherence",           "gte", 45.0),
        ("journaling_depth",        "gte", 40.0),
        ("focus_session_length",    "gte", 15.0),
        ("goal_completion_rate",    "gte", 20.0),
        ("emotional_arc_stability", "gte", 40.0),
    ],
    # Stage 3 → 4
    3: [
        ("decision_entropy",        "lt",  50.0),
        ("hrv_coherence",           "gte", 60.0),
        ("journaling_depth",        "gte", 60.0),
        ("focus_session_length",    "gte", 35.0),
        ("goal_completion_rate",    "gte", 45.0),
        ("emotional_arc_stability", "gte", 55.0),
    ],
    # Stage 4 → 5
    4: [
        ("decision_entropy",        "lt",  40.0),
        ("hrv_coherence",           "gte", 75.0),
        ("journaling_depth",        "gte", 80.0),
        ("focus_session_length",    "gte", 60.0),
        ("goal_completion_rate",    "gte", 70.0),
        ("emotional_arc_stability", "gte", 70.0),
    ],
}

# Regression markers: prior-stage thresholds reapplied in reverse
# Reuse ADVANCE_MARKERS[stage - 1] logic but check if score FAILS those
# thresholds (i.e., user has regressed toward prior-stage behavior).


def _evaluate_markers(
    scores: MarkerScores,
    marker_defs: list[tuple[str, str, float]],
) -> list[str]:
    """Return list of marker dimension names that are currently MET."""
    met: list[str] = []
    scores_dict = asdict(scores)
    for dim, op, threshold in marker_defs:
        value = scores_dict[dim]
        if op == "lt" and value < threshold:
            met.append(dim)
        elif op == "gte" and value >= threshold:
            met.append(dim)
    return met


# ---------------------------------------------------------------------------
# StageEvaluator
# ---------------------------------------------------------------------------

class StageEvaluator:
    """
    Stateless evaluation logic.

    Given a StageRecord and current MarkerScores, determines:
    - transition_candidate: 4+ advance markers met AND minimum window elapsed
    - regression_risk: 5+ regression markers met AND 14+ days sustained
    """

    def evaluate(
        self,
        record: StageRecord,
        scores: MarkerScores,
        regression_days_sustained: int = 0,
    ) -> tuple[bool, bool, list[str]]:
        """
        Returns (transition_candidate, regression_risk, markers_met).

        regression_days_sustained: how many consecutive days the prior-stage
        marker pattern has been sustained (caller tracks this externally or
        passes 0 if not applicable).
        """
        stage = record.current_stage
        days_in = record.days_in_stage

        # --- Advance evaluation ---
        advance_candidate = False
        markers_met: list[str] = []

        if stage < 5:
            marker_defs = ADVANCE_MARKERS.get(stage, [])
            markers_met = _evaluate_markers(scores, marker_defs)
            min_window = MIN_TRANSITION_WINDOW_DAYS.get((stage, stage + 1), 999)
            advance_candidate = (
                len(markers_met) >= ADVANCE_MARKER_THRESHOLD
                and days_in >= min_window
            )

        # --- Regression evaluation ---
        regression_risk = False
        if stage > 1:
            prior_defs = ADVANCE_MARKERS.get(stage - 1, [])
            # Regression: score FAILS the prior-stage advance markers
            # (i.e., user is back in prior-stage behavior territory)
            # We invert the prior-stage markers: dim met means FAILING advance
            prior_failing: list[str] = []
            scores_dict = asdict(scores)
            for dim, op, threshold in prior_defs:
                value = scores_dict[dim]
                # Failing = opposite of the advance condition
                if op == "lt" and value >= threshold:
                    prior_failing.append(dim)
                elif op == "gte" and value < threshold:
                    prior_failing.append(dim)
            regression_risk = (
                len(prior_failing) >= REGRESSION_MARKER_THRESHOLD
                and regression_days_sustained >= REGRESSION_WINDOW_DAYS
            )

        return advance_candidate, regression_risk, markers_met


# ---------------------------------------------------------------------------
# Shadow Engine Gate
# ---------------------------------------------------------------------------

def get_shadow_mode(stage: int) -> str:
    """
    Returns the Shadow Engine operating mode for the given stage.

    Stage 1 → 'off'
    Stage 2 → 'observation'
    Stage 3 → 'full'
    Stage 4 → 'synthesis'
    Stage 5 → 'collective'
    """
    return _SHADOW_MODE_MAP.get(stage, "off")


# ---------------------------------------------------------------------------
# StageEngine (SQLite-backed coordinator)
# ---------------------------------------------------------------------------

_DEFAULT_DB_PATH = Path.home() / ".gaia" / "stage_engine.db"


class StageEngine:
    """
    Stateful coordinator for the Stage Engine.

    Responsibilities:
    - Load and persist StageRecord per user to SQLite
    - Delegate scoring to MarkerScorer
    - Delegate evaluation to StageEvaluator
    - Emit transition events (ceremony flag, stage history write)
    - Handle regression labeling (e.g. 'Stage 3R')
    """

    def __init__(self, db_path: Path | str = _DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._scorer = MarkerScorer()
        self._evaluator = StageEvaluator()
        self._init_db()

    # --- DB Setup ---

    def _init_db(self) -> None:
        with self._conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stage_records (
                    user_id      TEXT PRIMARY KEY,
                    record_json  TEXT NOT NULL
                )
            """)

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    # --- Persistence ---

    def load(self, user_id: str) -> StageRecord:
        """Load existing StageRecord or create a default Stage 1 record."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT record_json FROM stage_records WHERE user_id = ?",
                (user_id,),
            ).fetchone()

        if row:
            return self._deserialize(row[0])

        # New user: default to Stage 1
        now = _utcnow()
        return StageRecord(
            user_id=user_id,
            current_stage=1,
            stage_entered_at=now,
            days_in_stage=0,
            marker_scores=MarkerScores(
                decision_entropy=80.0,
                hrv_coherence=20.0,
                journaling_depth=5.0,
                focus_session_length=10.0,
                goal_completion_rate=10.0,
                emotional_arc_stability=20.0,
            ),
        )

    def save(self, record: StageRecord) -> None:
        """Persist StageRecord to SQLite."""
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO stage_records (user_id, record_json)
                VALUES (?, ?)
                ON CONFLICT(user_id) DO UPDATE SET record_json = excluded.record_json
                """,
                (record.user_id, self._serialize(record)),
            )

    @staticmethod
    def _serialize(record: StageRecord) -> str:
        d = asdict(record)
        return json.dumps(d)

    @staticmethod
    def _deserialize(raw: str) -> StageRecord:
        d = json.loads(raw)
        d["marker_scores"] = MarkerScores(**d["marker_scores"])
        d["stage_history"] = [
            StageTransition(**t) for t in d.get("stage_history", [])
        ]
        return StageRecord(**d)

    # --- Core Update Loop ---

    def update(
        self,
        user_id: str,
        *,
        decision_entropy_raw: float,
        hrv_rmssd_ms: float,
        journal_word_count: float,
        focus_minutes_avg: float,
        goal_completion_pct: float,
        emotional_volatility_raw: float,
        regression_days_sustained: int = 0,
    ) -> StageRecord:
        """
        Main entry point. Scores markers, evaluates transitions/regressions,
        writes history if a transition fires, saves, and returns updated record.
        """
        record = self.load(user_id)

        scores = self._scorer.score(
            decision_entropy_raw=decision_entropy_raw,
            hrv_rmssd_ms=hrv_rmssd_ms,
            journal_word_count=journal_word_count,
            focus_minutes_avg=focus_minutes_avg,
            goal_completion_pct=goal_completion_pct,
            emotional_volatility_raw=emotional_volatility_raw,
        )
        record.marker_scores = scores

        advance, regress, markers_met = self._evaluator.evaluate(
            record, scores, regression_days_sustained
        )

        record.transition_candidate = advance
        record.regression_risk = regress

        if advance and record.current_stage < 5:
            self._apply_advance(record, markers_met)

        elif regress and record.current_stage > 1:
            self._apply_regression(record)

        self.save(record)
        return record

    def _apply_advance(self, record: StageRecord, markers_met: list[str]) -> None:
        from_stage = record.current_stage
        to_stage = from_stage + 1
        now = _utcnow()

        transition = StageTransition(
            from_stage=from_stage,
            to_stage=to_stage,
            transitioned_at=now,
            markers_met=markers_met,
            ceremony_shown=False,
            label="",
        )
        record.stage_history.append(transition)
        record.current_stage = to_stage
        record.stage_entered_at = now
        record.days_in_stage = 0
        record.transition_candidate = False
        record.regression_risk = False

    def _apply_regression(self, record: StageRecord) -> None:
        from_stage = record.current_stage
        to_stage = from_stage - 1
        now = _utcnow()
        label = f"{from_stage}R"  # e.g. '3R' — information, not failure

        transition = StageTransition(
            from_stage=from_stage,
            to_stage=to_stage,
            transitioned_at=now,
            markers_met=[],
            ceremony_shown=False,
            label=label,
        )
        record.stage_history.append(transition)
        record.current_stage = to_stage
        record.stage_entered_at = now
        record.days_in_stage = 0
        record.transition_candidate = False
        record.regression_risk = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()
