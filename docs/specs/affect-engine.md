# Affect Engine — Design Specification
**Issue:** #65  
**Branch:** `feat/stage-engine-63`  
**Status:** Implementation complete (heuristics, NLP backend layer, ArcTrend, router, tests)

---

## 1. Purpose

The Affect Engine infers the user's emotional state from free-text input (journal entries, GAIA chat), stores snapshots in SovereignMemory, and provides rolling arc trend analytics for Stage Engine (#63) and Shadow Engine (#67).

All inference is **local-first** — no text ever leaves the device.

---

## 2. Inference Pipeline

```
  Text input
      │
      ▼
  AffectBackend.analyze(text)
      │
      ▼
  AffectAnalysisResult
  { label, confidence, PadVector, entropy, explanation }
      │
      ▼
  AffectEngine.analyze_text()
      ├─ compute arc_stability from valence history
      └─ persist AffectSnapshot to SovereignMemory
      │
      ▼
  AffectSnapshot → caller / Stage Engine / Shadow Engine
```

---

## 3. Emotion Model

GAIA uses a **7-class model** mapped to the Plutchik primary wheel:

| Label | Pleasure | Arousal | Dominance |
|---|---|---|---|
| joy | 0.80 | 0.62 | 0.70 |
| sadness | −0.72 | 0.22 | 0.22 |
| anger | −0.70 | 0.80 | 0.72 |
| fear | −0.76 | 0.86 | 0.18 |
| disgust | −0.65 | 0.46 | 0.58 |
| surprise | 0.05 | 0.88 | 0.50 |
| neutral | 0.00 | 0.10 | 0.50 |

PAD (Pleasure–Arousal–Dominance) values are fixed anchor points per the
Russell circumplex model, with a small entropy-based dominance adjustment.

---

## 4. NLP Backends

### 4.1 Heuristic (default)
Keyword lexicon (7 categories × 6–15 words) + PAD anchors.  Zero dependencies.  Deterministic.  Active now.

**Confidence formula:** `min(0.95, 0.45 + (best_score / len(tokens)) * 4.0)`

**Neutrality-first routing:**
1. If empty text → neutral, confidence=0.99
2. If procedural tokens dominate (≥1 match) and no emotional tokens → neutral, confidence=0.90
3. If no emotional tokens at all → neutral, confidence=0.78
4. Otherwise → highest-scoring emotion label

### 4.2 SBERT (upgrade path)
`roberta-base-go_emotions` via HuggingFace Transformers pipeline.
- Install: `pip install transformers torch`
- Model: ~500 MB download (cached after first run)
- Latency: ~40–120 ms per text on CPU
- GoEmotions 28 labels → GAIA 7-class via `_GOEMO_MAP`
- Falls back to Heuristic if import fails
- Enable: `GAIA_AFFECT_BACKEND=sbert`

### 4.3 LLM (local inference)
Prompt-based via llama.cpp HTTP server.
- URL: `GAIA_LLM_URL` env var (default `http://localhost:8080`)
- Returns strict JSON: `{label, confidence, pleasure, arousal, dominance}`
- Timeout: 5 seconds; falls back to Heuristic on any error
- Enable: `GAIA_AFFECT_BACKEND=llm`

---

## 5. ArcTrend

Computed from last 30 days of valence/arousal/emotion history.

| Output | Formula / Rule |
|---|---|
| `valence_trend` | OLS slope of 30-day valence series, clipped to [−1, 1] |
| `mood_momentum` | `mean(v[-7:]) − mean(v[-30:])`, clipped to [−1, 1] |
| `volatility` | `pstdev(v[-30:])` |
| `is_volatile` | `volatility > 0.35` |
| `dominant_emotion` | Modal label in last 30 snapshots |
| `low_energy_flag` | 7-day mean arousal < 0.25 |
| `arc_stability` | `exp(−2.5σ) × (1 − 0.8 × zcr)` — same formula as Stage Engine marker 6 |

ArcTrend is the primary feed to **Shadow Engine** (#67) for determining
which shadow archetype is currently active and how deep the shadow pattern runs.

---

## 6. HTTP API

| Method | Path | Description |
|---|---|---|
| GET | /affect/health | Liveness probe |
| POST | /affect/analyze | Run inference + optional persist |
| GET | /affect/history/{principal_id} | Raw biometric history |
| GET | /affect/trend/{principal_id} | ArcTrend for last N days |

`POST /affect/analyze` accepts an optional `backend` field to override the default per-request.

---

## 7. File Layout

```
src-python/affect_engine/
  __init__.py        ← public surface
  types.py           ← EmotionLabel, PadVector, AffectSnapshot, AffectAnalysisResult
  heuristics.py      ← lexicon, PAD anchors, analyze_text_heuristic()
  nlp_backend.py     ← AffectBackend ABC, HeuristicBackend, SBERTBackend, LLMBackend, build_backend()
  arc_trend.py       ← ArcTrend dataclass, compute_arc_trend(), _ols_slope()
  engine.py          ← AffectEngine — orchestrates analyze_text() + arc stability
  router.py          ← FastAPI router (/affect/analyze, /history, /trend, /health)
tests/
  test_affect_engine.py  ← 25 test classes
docs/specs/
  affect-engine.md   ← this file
```

---

## 8. Shadow Engine Integration

Shadow Engine (#67) reads `ArcTrend` from `GET /affect/trend/{principal_id}` and uses:

| ArcTrend field | Shadow Engine use |
|---|---|
| `dominant_emotion` | Maps to shadow archetype (e.g. chronic sadness → Orphan) |
| `is_volatile` | Flags active emotional turbulence → elevates shadow intensity |
| `low_energy_flag` | Maps to Martyr / Victim archetype pattern |
| `mood_momentum` | Negative momentum → shadow pattern strengthening |
| `valence_trend` | Sustained negative trend → deep shadow activation |

---

## 9. Acceptance Criteria

- [ ] `pytest tests/test_affect_engine.py` passes with zero failures
- [ ] Heuristic labels all 7 emotions correctly on representative inputs
- [ ] `build_backend("unknown")` returns HeuristicBackend without error
- [ ] `GAIA_AFFECT_BACKEND=sbert` selects SBERTBackend (falls back gracefully if not installed)
- [ ] ArcTrend ascending series → positive `valence_trend`
- [ ] ArcTrend oscillating series → `is_volatile=True`
- [ ] ArcTrend empty inputs return safe defaults (no exception)
- [ ] `GET /affect/trend/{id}` returns valid ArcTrend JSON
- [ ] `POST /affect/analyze` with `persist=false` does not write to SovereignMemory
