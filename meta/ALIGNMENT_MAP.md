# GAIA Alignment Map

**Version:** 1.0
**Created:** 2026-06-30
**Purpose:** Cross-document tension matrix. Shows which canon docs interact, which conflict, and the resolution status of each tension.

---

## System Layer Map

```
GAIA-OS Stack (top to bottom)
┌────────────────────────────────────────────────────┐
│  GOVERNANCE LAYER         C157 (GCS, criticality)      │  ✅ Validated SIM-001
├────────────────────────────────────────────────────┤
│  AGENT LAYER              C155 (8-agent stack, loop)   │  🚨 CT-003 BLOCKING
├────────────────────────────────────────────────────┤
│  KNOWLEDGE LAYER          C156 (KG, memory schema)     │  ⚠️ CT-002 + CT-005
├────────────────────────────────────────────────────┤
│  METRICS LAYER            C160 (all system metrics)    │  ⚠️ CT-001 + CT-002
├────────────────────────────────────────────────────┤
│  PRIVACY LAYER            C139 + C158 (consent, GDPR)  │  ⚠️ CT-004
├────────────────────────────────────────────────────┤
│  HARDWARE LAYER           BIOPHOTON_09 (CP-3 transducer)│  ⚠️ CT-001
└────────────────────────────────────────────────────┘
```

---

## Cross-Document Tension Matrix

| Doc A | Doc B | Tension | CT-ID | Status |
|---|---|---|---|---|
| BIOPHOTON_09 | C160 | BCI stage params cannot hit Metric 26 ≥70% target | CT-001 | ⏳ Awaiting decision |
| C156 | C160 | Memory schema has no access-boosting; Metric 6 ≥85% unachievable | CT-002 | ⏳ Awaiting decision |
| C155 | C155 | Agent spec allows 7% cascade failure + false safety signal at baseline | CT-003 | ⏳ Awaiting decision |
| C139 | C158 | Single-node ledger cannot sustain GDPR erasure compliance at scale | CT-004 | ⏳ Awaiting decision |
| C156 | C156 | KG schema has no maintenance layer; provenance collapses cycle 29 | CT-005 | ⏳ Awaiting decision |
| C157 | — | GCS safe band thresholds | — | ✅ Validated SIM-001 |
| C155 | — | Living Architecture Loop convergence | — | ✅ Validated SIM-007 |
| C156 | — | Edge contradiction logic | — | ✅ Validated SIM-006 |

---

## Document Health Status

| Canon Doc | Name | Health | Open CTs | Validated aspects |
|---|---|---|---|---|
| C139 | Consent Ledger | ⚠️ Needs update | CT-004 | Core consent logic ✅ |
| C154 | (TBD) | ❓ Not yet simulated | — | — |
| C155 | Agent Architecture | 🚨 Blocking issue | CT-003 | Living Architecture Loop ✅ |
| C156 | Knowledge/Memory | ⚠️ Needs update | CT-002, CT-005 | Edge contradiction logic ✅ |
| C157 | Criticality / GCS | ✅ Healthy | None | GCS band, tipping point ✅ |
| C158 | GDPR Compliance | ⚠️ Needs update | CT-004 | — |
| C160 | System Metrics | ⚠️ Needs update | CT-001, CT-002 | — |
| BIOPHOTON_09 | Photonic Hardware | ⚠️ Needs update | CT-001 | — |

---

## Research → Canon Pipeline

| Research Doc | Status | Feeds Into | Canon Impact |
|---|---|---|---|
| R-001: Unified Cognitive Architecture | ✅ Committed | C155, C156, C157 | Roadmap input |
| R-002: Long-Term Memory Framework | ✅ Committed | C156, C160, C139 | Feeds CT-002 resolution |
| R-003 to R-008 | ⏳ Awaiting delivery | TBD | TBD |

---

## Simulation → Canon Pipeline

| Simulation | Validates or Challenges | Canon Doc | Resolution Sim Needed |
|---|---|---|---|
| SIM-001 | ✅ Validates | C157 | None |
| SIM-002 | ⚠️ Challenges | BIOPHOTON_09, C160 | SIM-008 (after CT-001 fix) |
| SIM-003 | ⚠️ Challenges | C156, C160 | SIM-009 (after CT-002 fix) |
| SIM-004 | 🚨 Challenges | C155 | SIM-010 (after CT-003 fix) |
| SIM-005 | ⚠️ Challenges | C139, C158 | SIM-011 (after CT-004 fix) |
| SIM-006 | ⚠️ Challenges + ✅ Partial | C156 | SIM-012 (after CT-005 fix) |
| SIM-007 | ✅ Validates | C155 | None |
| SIM-013–015 | ⏳ Queued | All layers | After all CTs resolved |

---

*Alignment Map v1.0 — 2026-06-30. Living document. Update after every CT resolution.*
