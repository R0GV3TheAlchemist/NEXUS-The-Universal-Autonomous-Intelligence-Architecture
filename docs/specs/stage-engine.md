# Stage Engine — Design Specification
**Issue:** #63  
**Branch:** `feat/stage-engine-63`  
**Status:** Implementation complete (marker formulas, transition gates, Schumann integration, window tracker, router, tests)

---

## 1. Purpose

The Stage Engine tracks a user's alchemical developmental stage (1–5) by scoring six behavioural markers daily, applying time-gated forward/regression rules, and persisting state to SovereignMemory.  It is the central arbiter of which GAIA features are available and how the UI persona is toned.

---

## 2. The Five Stages

| Stage | Name | Archetype | Minimum days to next |
|---|---|---|---|
| 1 | Divergence | Nigredo — dissolution | 21 |
| 2 | Awakening | Albedo — purification | 30 |
| 3 | Crucible | Citrinitas — illumination | 45 |
| 4 | Convergence | Rubedo — integration | 60 |
| 5 | Ascendence | Magnum Opus — completion | — |

---

## 3. The Six Markers

### 3.1 Decision Entropy  (0–100, higher = more decisive)

Shannon entropy over daily goal-state distribution.

\[
H = -\sum_{i} p_i \log_2 p_i, \quad H_{max} = \log_2(5)
\]

\[
\text{score} = \left(1 - \frac{H}{H_{max}}\right) \times 100
\]

Goal states: `committed | reversed | abandoned | not_set | completed`.

### 3.2 HRV Coherence  (0–100)

Personalised z-score of today's RMSSD against 30-day history, passed through a sigmoid, then blended with the Schumann alignment score.

\[
c_{hrv} = \sigma(z), \quad z = \frac{hrv_{today} - \mu_{30}}{\sigma_{30}}
\]

\[
\text{score} = (0.7 \times c_{hrv} + 0.3 \times \overline{alignment}_{30}) \times 100
\]

The 0.30 Schumann weight means this marker directly reflects planetary EM alignment — the only marker that does so by design.

### 3.3 Journaling Depth  (0–100)

14-day moving average of a weighted composite:

| Component | Weight |
|---|---|
| `len_norm` = min(token_count / 1200, 1) | 0.25 |
| `lexical_entropy` | 0.30 |
| `self_ref_ratio` | 0.25 |
| `emotion_density` | 0.20 |

### 3.4 Focus Session Length  (0–100)

14-day median session mapped through a piecewise linear scale:

| Median (min) | Score |
|---|---|
| ≤ 5 | 0 |
| 25 | 60 |
| 50 | 80 |
| ≥ 90 | 100 |

### 3.5 Goal Completion Rate  (0–100)

Bayesian-smoothed completion rate:

\[
\text{score} = \frac{\text{completed} + 1}{\text{completed} + \text{abandoned} + 2} \times 100
\]

The +1 / +2 Laplace prior prevents division by zero and avoids 0% or 100% extremes with small samples.

### 3.6 Emotional Arc Stability  (0–100)

Exponential decay of standard deviation combined with zero-crossing rate penalty:

\[
\text{stability} = e^{-2.5 \sigma} \times (1 - 0.8 \times \text{zcr})
\]

\[
\text{score} = \text{stability} \times 100
\]

where `zcr` = fraction of consecutive sign changes in the valence series.

---

## 4. Forward Transition Thresholds

All six markers are evaluated.  A forward transition fires when **≥ 4 of 6** markers meet the stage threshold AND the sustained window (in days) is met.

| Marker | 1→2 | 2→3 | 3→4 | 4→5 |
|---|---|---|---|---|
| decision_entropy | 30 | 40 | 55 | 60 |
| hrv_coherence | 40 | 45 | 55 | 60 |
| journaling_depth | 35 | 50 | 60 | 65 |
| focus_session_length_min | 35 | 45 | 55 | 60 |
| goal_completion_rate | 25 | 40 | 60 | 70 |
| emotional_arc_stability | 30 | 40 | 55 | 65 |
| **Minimum days sustained** | **21** | **30** | **45** | **60** |

---

## 5. Regression Rules

Regression fires when **≥ 5 of 6** markers have dropped below the entry threshold for the current stage for **≥ 14 consecutive days**.

A marker is "regression-active" when it falls below the threshold that was required to enter the current stage (i.e. the `(prior_stage → current_stage)` forward threshold).

---

## 6. Schumann Integration

The Schumann Alignment Layer (#64) feeds the Stage Engine via `schumann_bridge.py`:

```
SchumannState.to_stage_dict()
        ↓
schumann_to_alignment(state)
        ↓
  alignment_score_100  →  appended to alignment_score_history
  env_modifier (0.8–1.0)  →  returned in /stage/evaluate response metadata
```

| Schumann disturbance_level | env_modifier |
|---|---|
| stable | 1.00 |
| elevated | 0.95 |
| disturbed | 0.85 |
| unavailable | 1.00 (neutral) |

When `confidence < 0.4` (is_trusted = False), the bridge always returns alignment = 50 and modifier = 1.0 — no Schumann effect on stage scoring.

---

## 7. Window Tracker

`WindowTracker` persists `days_forward_window_met` and `days_regression_window` in a `stage_window_state` table (SovereignMemory).  It increments once per calendar day and resets to 0 whenever the condition is no longer met.  Multiple calls on the same day are idempotent.

---

## 8. HTTP API

| Method | Path | Description |
|---|---|---|
| GET | /stage/health | Liveness probe |
| GET | /stage/record/{principal_id} | Current StageRecord as JSON |
| GET | /stage/history/{principal_id} | List of past StageTransitions |
| POST | /stage/evaluate | Full evaluation tick + optional Schumann input |

`POST /stage/evaluate` accepts an optional `schumann_state` dict (from `SchumannState.to_stage_dict()`).  When provided, `alignment_score` is appended to the history and `env_modifier` is returned in `response.meta`.

---

## 9. File Layout

```
src-python/stage_engine/
  __init__.py          ← public surface
  types.py             ← Stage, MarkerScores, StageRecord, StageTransition, TransitionResult
  markers.py           ← MarkerScorer (6 static methods + .compute())
  transitions.py       ← FORWARD_THRESHOLDS, check_forward_transition(), check_regression()
  engine.py            ← StageEngine (evaluate, _score_only, persistence helpers)
  schumann_bridge.py   ← schumann_to_alignment() — Schumann ↔ Stage Engine adapter
  window_tracker.py    ← WindowTracker — persists daily window counters
  router.py            ← FastAPI router (/stage/evaluate, /record, /history, /health)
tests/
  test_stage_engine.py ← 18 test classes, ~35 assertions
docs/specs/
  stage-engine.md      ← this file
```

---

## 10. Acceptance Criteria

- [ ] `pytest tests/test_stage_engine.py` passes with zero failures
- [ ] All six marker scores bounded to [0, 100]
- [ ] Forward transition blocked until both window and marker count are met
- [ ] Regression fires only after 14-day window with ≥ 5 markers dropped
- [ ] Schumann bridge returns neutral (50, 1.0) when state is None or untrusted
- [ ] `disturbed` Schumann state → env_modifier = 0.85
- [ ] WindowTracker increments once per day, resets when condition breaks
- [ ] `GET /stage/record/{id}` returns 404 for unknown principal
- [ ] `POST /stage/evaluate` with schumann_state appends to alignment_history
- [ ] All StageTransition labels include stage number and name
