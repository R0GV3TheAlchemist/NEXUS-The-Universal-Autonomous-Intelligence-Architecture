# GAIA Affective Mirror — Canonical Specification

**Issue**: #161  
**Module**: `core/affective_mirror.py`  
**Branch**: `feat/affective-mirror-161`  
**Status**: ✅ Implemented

---

## Purpose

The Affective Mirror gives GAIA real-time awareness of the user's emotional state through three non-invasive, fully-local channels: voice prosody, biometric inference, and text sentiment. A fourth optional channel (facial micro-expression via MorphCast) is architecturally wired in but requires explicit opt-in. All processing is 100% local — no emotional data ever leaves the device.

This module feeds:
- **SoulMirror** (Issue #97) — reflective dialogue adaptation
- **Stage Engine** (Issue #85) — ceremony mode routing
- **Crystal Knowledge Graph** (Issue #162) — `emotional_context` on every memory node
- **Sentient Interruption Gate** (Issue #164) — receptivity scoring
- **Conscious Workspace** (Issue #163) — crisis mode transition
- **SessionModeManager** (Issue #168) — biometric session mode suggestions
- **StateAdapter** (Issue #172) — cross-engine affective state bus

---

## Architecture

```
VoiceProsodyAnalyzer  ──┐
BiometricAffectInference─┤── AffectiveFusion ──> AffectiveState
TextSentimentAnalyzer  ──┤       │
FacialAnalyzer (opt-in)──┘       ├──> EmotionalArcTracker (longitudinal)
                                 ├──> CrisisDetector (convergence watchdog)
                                 └──> SoulMirrorAffectBridge (pub/sub)
```

`AffectiveMirror` is the top-level façade that wires all sub-systems.

---

## Data Model

### AffectiveState (frozen dataclass)

| Field | Type | Notes |
|---|---|---|
| `state_id` | `str` | uuid4 |
| `timestamp` | `datetime` | UTC |
| `primary_emotion` | `EmotionLabel` | 14-category taxonomy |
| `secondary_emotion` | `Optional[EmotionLabel]` | runner-up in fusion vote |
| `valence` | `float [-1, 1]` | negative ↔ positive |
| `arousal` | `float [-1, 1]` | calm ↔ activated |
| `confidence` | `float [0, 1]` | fusion confidence |
| `channels_used` | `Tuple[AffectiveChannel, ...]` | which channels contributed |
| `biometric_coherence` | `Optional[float]` | HRV ms if available |
| `planetary_context` | `Optional[str]` | Schumann label if available |
| `gaian` | `Optional[str]` | active Gaian |
| `trace_id` | `Optional[str]` | GAIATrace correlation id |

### EmotionLabel (14 categories)

`calm`, `focused`, `curious`, `elated`, `content`, `anxious`, `stressed`,
`fatigued`, `grief`, `anger`, `fear`, `dissociated`, `overwhelmed`, `crisis`

### AffectiveChannel

`voice_prosody`, `biometric`, `facial`, `text_sentiment`, `manual`

---

## Fusion Strategy

1. **Crisis override**: if ANY channel returns `EmotionLabel.CRISIS` with
   confidence ≥ 0.70, primary becomes `CRISIS` immediately.
2. **Weighted mean** for valence and arousal (weighted by per-channel confidence).
3. **Plurality vote** for primary emotion. Second-highest vote → secondary.

---

## Crisis Detection

A `CrisisMarker` is raised when ≥ 2 channels simultaneously report:
- emotion in `{crisis, overwhelmed, dissociated, fear, grief}`, OR
- valence ≤ −0.65 AND arousal ≥ +0.75

The caller decides what to do. GAIA never forces action — Canon C01 (Sovereignty).
The only exception: `SessionModeManager` may transition to Crisis mode
automatically but the user can dismiss it.

---

## Longitudinal Arc

`EmotionalArcTracker` keeps a rolling window of up to 200 `AffectiveState` samples
and computes:
- **Valence trend**: IMPROVING / STABLE / DECLINING / VOLATILE
- **Sustained crisis**: True if last N (default 3) states are all crisis-adjacent
- **Arc summary**: serialised list for Crystal graph nodes

---

## Voice Prosody Features

| Feature | Description |
|---|---|
| `mfcc_valence_score` | Model-derived valence from MFCCs [-1, 1] |
| `energy_rms` | RMS frame energy [0, 1] |
| `speech_rate_wpm` | Words per minute |
| `pause_ratio` | Fraction of silence [0, 1] |
| `pitch_std_hz` | Pitch variability (tremor proxy) |
| `pitch_mean_hz` | Fundamental frequency |
| `zcr_mean` | Zero-crossing rate |

In production: wraps openSMILE or MorphCast Emotion AI WebView.
Fallback: heuristic rules (confidence 0.50 vs. model confidence 0.70).

---

## Biometric Affect Inference

Maps RMSSD (HRV ms), SpO₂, EDA (skin conductance µS),
and Personal Coherence Score (Issue #153) → valence/arousal/emotion.

Research basis: XR-DMT Study (2025) — HRV + EDA + real-time AI enables
non-pharmacological anxiety interventions with measurable biometric outcomes.

---

## SoulMirrorAffectBridge

Thin pub/sub bridge — no circular imports. Sub-systems register via:

```python
mirror.bridge.subscribe(callback)         # sync
mirror.bridge.subscribe_async(coro)       # async
```

Every `AffectiveState` update is broadcast to all registered subscribers.

---

## Integration Points

| System | Integration |
|---|---|
| `core.state_adapter.StateAdapter` | Subscribe to bridge; publish `AffectiveStateKind` |
| `core.soul_mirror_engine` | Subscribe to bridge; adapt dialogue tone |
| `core.stage_bridge` | Subscribe; trigger ceremony/crisis Stage Engine mode |
| `core.trace.GAIATrace` | Pass `trace_id` into `ingest_multi()` |
| Crystal graph nodes | `emotional_context` field = `str(state.primary_emotion)` |
| `SessionModeManager` (Issue #168) | Subscribe; trigger REST/CRISIS suggestions |

---

## CLI Usage

```bash
# Print current fused affective state
python -m core.affective_mirror status

# Print last 10 arc points
python -m core.affective_mirror history --n 10

# Print active crisis markers
python -m core.affective_mirror crisis

# Run 5-step synthetic demo
python -m core.affective_mirror demo
```

---

## Test Coverage Checklist

- [ ] `VoiceProsodyAnalyzer.analyze()` — 6 scenario feature dicts → correct EmotionLabel
- [ ] `BiometricAffectInference.analyze()` — low HRV + high EDA → OVERWHELMED
- [ ] `TextSentimentAnalyzer.analyze()` — crisis keyword → CRISIS with confidence ≥ 0.85
- [ ] `AffectiveFusion.fuse()` — crisis override fires when ANY channel CRISIS ≥ 0.70
- [ ] `AffectiveFusion.fuse()` — weighted mean valence correct to 2dp across 3 channels
- [ ] `EmotionalArcTracker.current_trend()` — IMPROVING / DECLINING / VOLATILE all tested
- [ ] `EmotionalArcTracker.sustained_crisis()` — returns True after N consecutive crisis states
- [ ] `CrisisDetector.evaluate()` — marker fired at exactly 2 converging channels
- [ ] `CrisisDetector.evaluate()` — marker NOT fired for single-channel crisis
- [ ] `SoulMirrorAffectBridge.publish()` — all registered sync callbacks called
- [ ] `SoulMirrorAffectBridge.publish_async()` — all async callbacks awaited
- [ ] `AffectiveMirror.ingest_multi()` — end-to-end: readings → state → arc → bridge
- [ ] Bridge callback exception does NOT propagate (C30)
- [ ] Crisis callback exception does NOT propagate (C30)
- [ ] All `__all__` names importable from `core.affective_mirror`

---

## Canon

- **C29** (Embodiment) — the OS is aware of how the body feels in real-time
- **C01** (Sovereignty) — 100% local; user controls opt-in channels; GAIA never forces action
- **C05** (Transparency) — every AffectiveState carries `channels_used`; nothing hidden
- **C30** (No silent failures) — crisis never missed; callback exceptions never swallowed silently

---

## Related Issues

- Depends on: #153 (Biometric Coherence Engine), #159 (Voice — prosody feed)
- Feeds: #97 (Soul Mirror), #85 (Stage Engine), #162 (Crystal — emotional_context)
- Feeds: #164 (Sentient Interruption — receptivity), #163 (Workspace — crisis mode)
- Feeds: #168 (Biometric Session Modes — REST/CRISIS suggestions)
- Feeds: #172 (State Adapter — affective channel)
