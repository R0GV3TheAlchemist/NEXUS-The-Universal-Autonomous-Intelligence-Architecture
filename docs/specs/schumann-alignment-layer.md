# Schumann Alignment Layer — Design Specification
**Issue:** #64  
**Branch:** `feat/schumann-alignment-64`  
**Status:** In progress

---

## 1. Purpose

The Schumann Alignment Layer ingests planetary electromagnetic signal data
(Schumann resonances, geomagnetic indices), normalises it against rolling
baselines, classifies the planetary EM environment, and emits a typed
`SchumannState` snapshot that the Stage Engine (#63) uses as one of its
environmental inputs.

It is **not** a mood or consciousness model. It is a signal quality,
stability, and environmental-context service.

---

## 2. File Layout

```
src-python/
  schumann/
    __init__.py       ← public API surface
    models.py         ← PlanetarySignalSample, SchumannState, DisturbanceLevel
    sources.py        ← source adapters (dev, noaa_ftp stub, local_sensor stub)
    engine.py         ← SchumannEngine — ingestion, processing, scoring
    router.py         ← FastAPI router (GET /state, GET /health, WS /stream)
    dev_dataset.py    ← CLI/Python to generate synthetic CSV for tests
tests/
  test_schumann.py    ← pytest suite (9 test classes, ~25 assertions)
docs/specs/
  schumann-alignment-layer.md  ← this file
```

---

## 3. Data Contracts

### 3.1 PlanetarySignalSample (raw input)

| Field       | Type     | Description |
|-------------|----------|-------------|
| timestamp   | datetime | UTC, must be timezone-aware |
| channel     | str      | Logical channel name (see §3.3) |
| value       | float    | Measured value in `unit` |
| unit        | str      | SI unit string |
| source      | str      | Adapter ID |
| quality     | float    | 0.0–1.0 (1.0 if source has no quality flags) |

### 3.2 SchumannState (Stage Engine contract)

| Field                | Type            | Range / Notes |
|----------------------|-----------------|---------------|
| timestamp            | datetime        | UTC |
| fundamental_hz       | float           | ~7.0–8.5 Hz |
| harmonic_power       | dict[str,float] | Keys: f1–f5; values 0–1 |
| geomagnetic_activity | float           | 0.0 (quiet) – 1.0 (severe) |
| signal_quality       | float           | 0.0–1.0 |
| disturbance_level    | DisturbanceLevel| stable \| elevated \| disturbed \| unavailable |
| alignment_score      | float           | 0.0–1.0 (see §4) |
| confidence           | float           | 0.0–1.0 |
| source_ids           | list[str]       | Contributing adapters |
| baseline_hz          | float           | 24h rolling mean of sr_f1_freq |
| deviation_sigma      | float           | Current σ deviation from baseline |
| experimental_flags   | dict[str,float] | Feature-gated; must not affect core logic |

### 3.3 Canonical Channel Names

| Channel      | Unit      | Description |
|--------------|-----------|-------------|
| sr_f1_freq   | Hz        | Schumann fundamental instantaneous frequency |
| sr_f1        | pT_norm   | Fundamental amplitude (normalised) |
| sr_f2        | pT_norm   | 2nd harmonic amplitude |
| sr_f3        | pT_norm   | 3rd harmonic amplitude |
| sr_f4        | pT_norm   | 4th harmonic amplitude |
| sr_f5        | pT_norm   | 5th harmonic amplitude |
| geomag_kp    | index     | Planetary K-index (0–9 normalised to 0–1) |
| geomag_dst   | nT        | Storm-time Dst index (future) |

---

## 4. Alignment Score Formula

```
alignment_score = 0.45 × stability
               + 0.30 × harmonic_coherence
               + 0.25 × signal_quality
```

Where:
- **stability** = `max(0, 1 - min(|deviation_sigma| / 4, 1))`
- **harmonic_coherence** = mean of `harmonic_power` values (f1–f5), clamped to [0,1]
- **signal_quality** = mean of per-sample quality flags in the active window

The result is clamped to [0.0, 1.0].  Confidence is computed separately and
must not be conflated with alignment_score.

---

## 5. Disturbance Classification

| Condition | Level |
|-----------|-------|
| No data OR signal_quality < 0.2 | UNAVAILABLE |
| \|deviation\| > 2σ OR signal_quality < 0.5 | DISTURBED |
| \|deviation\| > 1σ | ELEVATED |
| Otherwise | STABLE |

---

## 6. Stage Engine Integration

Call `engine.tick()` on each Stage Engine clock cycle.  Check
`state.is_trusted` before using `state.alignment_score` as an input.
When `is_trusted is False` the Stage Engine should treat Schumann
input as advisory only (i.e. it cannot _raise_ the stage, only
_lower_ a disturbance penalty).

```python
state = await schumann_engine.tick()
if state.is_trusted:
    env_weight = state.alignment_score
else:
    env_weight = 0.5  # neutral fallback
```

---

## 7. HTTP API

| Method | Path               | Description |
|--------|--------------------|-------------|
| GET    | /schumann/state    | Current SchumannState as JSON |
| GET    | /schumann/health   | Liveness probe |
| WS     | /schumann/stream   | Push state every 5 s |

---

## 8. Source Adapters

| ID            | Status | Notes |
|---------------|--------|-------|
| dev           | ✅ Ready | Deterministic synthetic signal; no network; seed=42 |
| noaa_ftp      | 🔲 Stub | Implement FTP polling when activating |
| local_sensor  | 🔲 Stub | Requires hardware + driver layer |

---

## 9. Experimental Features

The following are feature-flagged (`SCHUMANN_EXPERIMENTAL=1` or
`EngineConfig(experimental=True)`) and placed only in
`SchumannState.experimental_flags`:

| Key                     | Description |
|-------------------------|-------------|
| quantum_bio_coupling    | Fröhlich condensation proxy — NOT COMPUTED (stub 0.0) |
| seismic_precursor_score | CNN-BiGRU output — NOT OPERATIONAL |
| laic_channel_state      | Lithosphere-Atmosphere-Ionosphere state — stub |

Core logic MUST NOT read or branch on these values.

---

## 10. Acceptance Criteria

- [ ] `pytest tests/test_schumann.py` passes with zero failures
- [ ] `SchumannEngine(EngineConfig(source="dev")).tick()` returns valid `SchumannState`
- [ ] `alignment_score` always in [0.0, 1.0]
- [ ] `confidence < 0.4` when engine has received no data
- [ ] `disturbance_level == UNAVAILABLE` when engine has no samples
- [ ] `experimental_flags == {}` when `experimental=False`
- [ ] Stage Engine can consume `state.to_stage_dict()` with no KeyError
- [ ] All endpoints in `router.py` return expected status codes
- [ ] Dev dataset CSV generated via `python -m schumann.dev_dataset`
