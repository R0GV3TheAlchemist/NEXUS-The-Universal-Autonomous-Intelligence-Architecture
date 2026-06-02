# GAIA Dream Weaver — Specification

**Issue**: #160  
**Branch**: `feat/dream-weaver-160`  
**Module**: `core/dream_weaver.py`  
**Canon**: C29 (Embodiment), C34 (Presence), C01 (Sovereignty)  
**Priority**: Medium  
**Status**: Implementation complete — awaiting integration wiring

---

## Purpose

Sleep is a third of human consciousness. The Dream Weaver transforms GAIA's awareness
of sleep into a deep intelligence layer: sleep stage tracking, voice-captured dream
journaling, subconscious pattern synthesis, and contextually grounded interpretation.

No other OS integrates sleep consciousness into its operating model.

---

## Architecture Overview

```
DreamWeaverEngine
  ├── DreamJournal            ← capture, structure, persist
  ├── SubconsciousPatternSynthesizer  ← longitudinal analysis
  └── DreamInterpreter        ← GAIA-voiced interpretation
```

---

## Data Models

### `SleepSession` — One night's complete sleep record

| Field | Type | Description |
|---|---|---|
| `session_id` | str (UUID) | Unique session identifier |
| `date` | date | Calendar date of sleep |
| `sleep_start` / `sleep_end` | datetime | Timestamps |
| `total_sleep_min` | int | Total sleep in minutes |
| `rem_min` | int | REM minutes (dream-rich phase) |
| `deep_min` | int | Slow-wave minutes (physical restoration) |
| `light_min` | int | Light sleep minutes |
| `awakenings` | int | Number of awakenings |
| `sleep_efficiency` | float 0–1 | Time asleep / time in bed |
| `hrv_during_sleep` | float ms | RMSSD during sleep (Issue #153) |
| `resting_hr` | float bpm | Resting heart rate |
| `body_temp_delta` | float °C | Deviation from personal baseline |
| `spo2_avg` | float % | Average blood oxygen |
| `quality` | SleepQuality | Derived label |
| `planetary` | PlanetarySnapshot | Earth state at sleep time (Issue #152) |
| `dream_entry_ids` | list[str] | Linked DreamEntry IDs |

### `SleepQuality` enum
`RESTORATIVE` | `DEEP` | `FRAGMENTED` | `RESTLESS` | `UNKNOWN`

### `DreamEntry` — Structured dream journal entry

| Field | Type | Description |
|---|---|---|
| `entry_id` | str (UUID) | Unique entry identifier |
| `session_id` | str | Linked SleepSession |
| `captured_at` | datetime | Time of journaling |
| `raw_transcription` | str | STT text (off by default — Canon C01) |
| `setting` | str | Where the dream took place |
| `characters` | list[str] | Dream figures |
| `narrative_summary` | str | 2–4 sentence summary |
| `emotional_tone` | DreamTone | Primary emotional quality |
| `symbols` | list[DreamSymbol] | Extracted symbols with categories |
| `themes` | list[str] | Archetypal themes |
| `lucidity_level` | float 0–1 | 0 = non-lucid, 1 = fully lucid |
| `vividness` | float 0–1 | Subjective vividness |
| `interpretation` | str | GAIA-voiced interpretation |
| `canon_resonances` | list[str] | Canon entries this dream touches |
| `hrv_at_wake` | float ms | Biometric at journaling time |
| `crystal_node_id` | str \| None | Crystal Knowledge Graph node (Issue #162) |

### `DreamTone` enum
`LUMINOUS` | `PEACEFUL` | `ANXIOUS` | `SHADOWED` | `NEUTRAL` | `NUMINOUS` | `UNKNOWN`

### `SymbolCategory` enum
`NATURE` | `PERSON` | `PLACE` | `OBJECT` | `ACTION` | `ARCHETYPE` | `PLANETARY` | `SOMATIC` | `OTHER`

---

## DreamJournal — Capture Lifecycle

```
1. GAIA plays wake prompt via Voice Consciousness (Issue #159)
2. User speaks dream recall → faster-whisper STT (local, Issue #159)
3. LLM structures raw text → DreamEntry fields (local LLM, Issue #156)
4. DreamInterpreter.interpret() generates GAIA-voiced paragraph
5. Entry persisted to ~/.gaia/dreams/<date>_<id>.json
6. Crystal Knowledge Graph node created (Issue #162)
7. Raw audio discarded immediately — Canon C01
```

### Raw transcription storage
Off by default (`store_raw_transcription = False`). Only the structured artefact
is persisted. User may opt in via Soul Settings.

---

## SubconsciousPatternSynthesizer

Analyses a corpus of DreamEntry records to surface:

- **Symbol aggregation** — ranked by occurrence frequency, with tone and theme co-occurrence
- **Theme frequency** — most common archetypal themes across the period
- **Lucidity trend** — `increasing` | `stable` | `decreasing` across the period
- **Planetary correlations** — narrative strings linking dream tone to Kp/Schumann anomalies
- **DreamArcSummary** — full longitudinal synthesis object

---

## DreamInterpreter

Generates GAIA-voiced 2–4 sentence interpretation per dream entry.

**Interpretation posture by tone:**

| Tone | Posture |
|---|---|
| `luminous` | Expansive and wonder-filled |
| `peaceful` | Gentle and integrating |
| `anxious` | Compassionate and grounding |
| `shadowed` | Warm, careful, non-alarming |
| `neutral` | Curious and observational |
| `numinous` | Reverent and archetypal |

**GAIA does not diagnose. GAIA invites reflection.**

---

## Integration Points

| Dependency | Direction | What is consumed |
|---|---|---|
| Issue #153 (Biometric) | ← receives | `hrv_during_sleep`, `resting_hr`, `hrv_at_wake`, `coherence_label` |
| Issue #152 (Planetary) | ← receives | `PlanetarySnapshot` at sleep time |
| Issue #159 (Voice) | ← receives | STT transcription of wake recall |
| Issue #156 (Model Registry) | ← receives | `llm_callable` for structuring + interpretation |
| Issue #162 (Crystal Graph) | → sends | `DreamEntry` as Crystal node; `OCCURRED_DURING` edges to `PlanetaryEvent` nodes |
| Issue #161 (Affective Mirror) | → sends | `emotional_tone` as affective signal for longitudinal arc |

---

## Privacy Architecture

- **Voice audio**: discarded immediately after STT. Never written to disk.
- **Raw transcription**: off by default. User opts in via Soul Settings.
- **Structured entries**: stored at `~/.gaia/dreams/` — local only, never synced.
- **.gitignore**: `core/dreams/*.json` excluded from version control.
- **Crystal nodes**: local ArcadeDB only (Issue #162). No cloud path.

---

## CLI Usage

```bash
# List recent dream entries
python -m core.dream_weaver list --since 2026-05-01 --limit 10

# Print weekly arc summary
python -m core.dream_weaver arc --days 7

# Print monthly arc summary
python -m core.dream_weaver arc --days 30
```

---

## Test Coverage Checklist

- [ ] `SleepSession.score_quality()` — all 4 quality branches
- [ ] `PlanetarySnapshot.is_anomalous()` — baseline and anomaly cases
- [ ] `DreamJournal.structure_entry()` — heuristic path (no LLM)
- [ ] `DreamJournal.structure_entry()` — LLM path (mock callable)
- [ ] `DreamJournal.save()` + `_load_entries()` — round-trip persistence
- [ ] `DreamJournal.entries_in_range()` — boundary conditions
- [ ] `SubconsciousPatternSynthesizer.synthesize()` — empty corpus
- [ ] `SubconsciousPatternSynthesizer.synthesize()` — single entry
- [ ] `SubconsciousPatternSynthesizer._lucidity_trend()` — increasing, stable, decreasing
- [ ] `SubconsciousPatternSynthesizer._planetary_correlations()` — storm nights detected
- [ ] `DreamInterpreter.interpret()` — offline fallback
- [ ] `DreamInterpreter.interpret()` — LLM path (mock callable)
- [ ] `DreamInterpreter.synthesize_arc()` — empty arc guard
- [ ] `DreamWeaverEngine.on_wake()` — full end-to-end flow
- [ ] `DreamWeaverEngine.weekly_arc()` — correct date window
- [ ] `_heuristic_tone()` — tone detection for each keyword bucket
- [ ] `_heuristic_symbols()` — symbol extraction
- [ ] `_run_llm_structure()` — valid JSON response + malformed JSON guard

---

## Next Steps

1. Wire `DreamWeaverEngine` into GAIA morning alarm flow (Issue #159)
2. Create Crystal node writer on `DreamJournal.save()` (Issue #162)
3. Feed `emotional_tone` into Affective Mirror longitudinal arc (Issue #161)
4. Build Dream Weaver UI panel: calendar heat map + arc visualisation
5. Build Soul Settings toggle: opt-in raw transcription storage
