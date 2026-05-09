# Schumann Alignment Sidecar — Architecture Notes

**Module:** `core/schumann_alignment.py`
**Issue:** [#64](../../issues/64) — Schumann Biometric Alignment Layer (Phase 2)
**Pillar:** Viriditas (Pillar II)
**Status:** ✅ Implemented — Phase 2 complete

---

## What this module does

`core/schumann_alignment.py` is the Python sidecar that owns the full
alignment computation pipeline:

```
[Wearable cache]      [Schumann feed]
       │                    │
  HRVNormalizer       SchumannParser
  (rolling 30-day     (rolling 30-day
   z-score, 0–100)     z-score, 0–100)
       │                    │
       └────────┬───────────┘
                ▼
        compute_alignment()
        hrv_score, schumann_score, solar_kp → 0–100
                ▼
        score_to_ui_tier()
        0–100 → minimal | core | standard | full | vibrant
                ▼
        AlignmentStateEmitter.compute()
        → AlignmentState (frozen dataclass)
        → .to_json() → Tauri IPC
```

---

## Core formula

```python
base       = 100 - abs(hrv_score - schumann_score)
kp_penalty = min(solar_kp * 3, 30)   # max 30-point penalty
score      = max(0, base - kp_penalty)
```

Source: `docs/knowledge/SCHUMANN_BIOMETRIC_ALIGNMENT_SPEC.md` §Step 3

---

## Failure / Fallback modes

| Condition | Behaviour |
|---|---|
| Wearable not connected | `hrv_score = 50` (neutral baseline), `hrv_unavailable` recorded |
| Schumann feed down | `schumann_score = 50` (neutral baseline), `schumann_unavailable` recorded |
| Both unavailable | `score = 50`, `ui_tier = standard`, `both_unavailable_standard_forced` recorded |
| Kp > 8 (storm) | `score = 0`, `ui_tier = minimal` (restorative), `kp_storm_X.X` recorded |

All fallback conditions are reflected in `AlignmentState.fallback_mode` (comma-separated string)
and logged at WARNING level.

---

## IPC contract

`AlignmentState.to_json()` emits:

```json
{
  "score": 74.5,
  "hrv_score": 62.3,
  "schumann_score": 50.0,
  "solar_kp": 2.1,
  "ui_tier": "full",
  "last_updated": "2026-05-09T12:59:00+00:00",
  "fallback_mode": ""
}
```

The Tauri frontend consumes this struct via `invoke('get_alignment_state')` and
passes it to `applyAlignmentTheme()` (Issue #68).

---

## What's next (Phase 3+)

| Phase | Module | Status |
|---|---|---|
| Phase 1 | Rust: `poll_schumann_feed()`, `fetch_kp_index()` | 🔲 Pending |
| Phase 2 | Python sidecar: this module | ✅ Done |
| Phase 3 | Wearable API adapters (HealthKit, Garmin, Oura, Polar) | 🔲 Pending |
| Phase 4 | TypeScript: `AlignmentState` interface, `applyAlignmentTheme()` | 🔲 Pending |
| Phase 5 | Privacy audit, zero-data-off-device verification | 🔲 Pending |
| Phase 6 | Full pytest + Playwright integration tests | 🔲 Pending |

---

*Cross-reference: `docs/knowledge/SCHUMANN_BIOMETRIC_ALIGNMENT_SPEC.md`,
`PILLARS.md` (Pillar II — Viriditas)*
