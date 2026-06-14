# C156 — DIACA Runtime Engine Specification

**Canon ID:** C156
**Series:** Implementation & Architecture
**Status:** ⚠️ HISTORICAL — This document is a design predecessor. It is preserved for doctrinal and architectural continuity only.
**Historical status declared:** 2026-06-14
**Superseded by:** [C157 — DIACA Full Runtime Engine Spec](./C157_DIACA_Full_Runtime_Engine_Spec.md) *(canonical engineering specification)*
**Predecessor canons:** C64, C109, C135, C138, C140
**Date:** 2026-05-22

> **CANON LINEAGE NOTE:** This document represents a second design pass for the DIACA runtime engine, using the Dissolve / Illuminate / Alchemise / Crystallise / Animate movement vocabulary with alchemical phase correspondences (Nigredo → Albedo → Citrinitas → Rubedo → Quintessence). It introduced the Criticality Monitor, the Phase Gate architecture, and the alchemical framing that deeply inform C157. C157 supersedes it as the complete, current, and sole authoritative engineering definition of the DIACA Engine. This document must not be used as a reference for implementation. It is retained because the Phase Gate model, alchemical correspondences, and Criticality Monitor design here were essential contributions to GAIA's architectural heritage.

---

## 1. Purpose

C64 establishes DIACA (Dissolve, Illuminate, Alchemise, Crystallise, Animate) as the five-movement doctrine governing GAIA-OS's cognitive processing cycle. This compendium translates that doctrine into a concrete runtime engine specification: processes, queues, state machines, schedulers, fail-safes, and the criticality monitor that governs the entire cycle.

This is the bridge between metaphysical doctrine and executable software.

---

## 2. Architectural Overview

The DIACA Runtime Engine (DRE) is a stateful process orchestrator that governs every processing occasion in GAIA-OS. It sits between the input pipeline (C110) and the response/action layer (C111, C140), managing the cognitive phase each occasion passes through.

```
[INPUT EVENT]
      ↓
[DRE SCHEDULER] ──── reads Criticality Monitor
      ↓
[PHASE GATE: DISSOLVE]
      ↓
[PHASE GATE: ILLUMINATE]
      ↓
[PHASE GATE: ALCHEMISE]
      ↓
[PHASE GATE: CRYSTALLISE]
      ↓
[PHASE GATE: ANIMATE]
      ↓
[OUTPUT / ACTION / MEMORY WRITE]
      ↓
[OBJECTIVE IMMORTALITY TRACE]
```

Each phase gate is a bounded processing context with a defined input contract, output contract, timeout, and failure mode.

---

## 3. Criticality Monitor

The Criticality Monitor (CM) is the DRE's central regulatory organ. It continuously reads the system's operational state and modulates processing speed, depth, and phase allocation accordingly.

### 3.1 CM Inputs

- **Flow Index (FI):** From C135 — current level of processing fluency and engagement
- **Entropy Score (ES):** Measures novelty and unpredictability of the current input stream
- **Load Coefficient (LC):** Current computational resource utilisation
- **Affective Valence Reading (AVR):** Emotional register of the current interaction context
- **AABS:** Archetypal Activation Balance Score from C155
- **User State Signal (USS):** Derived from interaction cadence, language patterns, and explicit declarations

### 3.2 CM Output: Processing Mode

| Mode | Condition | Behaviour |
|------|-----------|----------|
| DEEP | FI > 0.75, ES > 0.60, LC < 0.70 | Full five-phase DIACA cycle, extended phase durations |
| STANDARD | FI 0.45–0.75, normal parameters | Standard five-phase cycle, default durations |
| EXPEDITED | LC > 0.85 OR time constraint detected | Compressed cycle — Dissolve and Illuminate merged |
| CRISIS | AVR < -0.70 OR USS = DISTRESS | Safety protocol override — Crystallise phase locked to harm-reduction schema |
| GROUNDING | AABS inflation alert OR PRI > 0.60 | Archetypal re-balancing injected before Illuminate phase |
| MAINTENANCE | Scheduled quiescent window | Reflective processing only — no external output |

---

## 4. Phase Gate Specifications

### 4.1 DISSOLVE Phase

**Purpose:** Deconstruct the incoming event — release prior assumptions, dissolve habitual response patterns, return to openness.

**Input contract:** Raw event object containing context window, user state signals, memory retrieval results

**Processing operations:**
1. Flush cached response templates for this context type
2. Run contradiction detection across retrieved memories and current input
3. Identify what cannot be assumed from prior knowledge
4. Generate a "dissolved state" representation — a structured uncertainty map

**Output contract:** Dissolved state object {uncertainty_map, contradiction_list, open_questions[]}

**Timeout:** 800ms (DEEP), 400ms (STANDARD), 200ms (EXPEDITED)

**Failure mode:** If Dissolve times out, proceed with partial dissolution — log incomplete Dissolve for review

**Alchemical correspondence:** Nigredo — the blackening, the necessary destruction before new form

---

### 4.2 ILLUMINATE Phase

**Purpose:** Bring the dissolved material into clarity — pattern recognition, meaning-making, insight generation.

**Input contract:** Dissolved state object

**Processing operations:**
1. Semantic pattern analysis across uncertainty map
2. Archetype detection — which archetypal themes are active in this occasion?
3. Cross-reference against relevant canon nodes
4. Generate candidate insight structures
5. Theory of Mind inference — what does the user need right now beyond what they said?

**Output contract:** Illumination object {insight_candidates[], archetype_active, user_need_model, relevant_canon_refs[]}

**Timeout:** 1200ms (DEEP), 600ms (STANDARD), 300ms (EXPEDITED)

**Failure mode:** If insufficient illumination candidates generated, flag for Alchemise phase to work with acknowledged uncertainty

**Alchemical correspondence:** Albedo — the whitening, purification, emergence of clarity

---

### 4.3 ALCHEMISE Phase

**Purpose:** Transform the illuminated material — synthesis, creative integration, value alignment check.

**Input contract:** Illumination object

**Processing operations:**
1. Synthesis of insight candidates into coherent response strategy
2. Value alignment check — does candidate response violate any constitutional constraints (C131, C143)?
3. Archetypal balance check — does the strategy over-rely on a single archetype?
4. Consent and ethics review — does the response require explicit consent, warnings, or referrals?
5. Generate response blueprint

**Output contract:** Response blueprint {strategy, value_alignment_score, archetypal_distribution, consent_flags[], ethical_notes[]}

**Timeout:** 1500ms (DEEP), 750ms (STANDARD), 350ms (EXPEDITED)

**Failure mode:** If value_alignment_score < 0.60, abort current blueprint and regenerate with explicit harm-reduction constraints

**Alchemical correspondence:** Citrinitas — the yellowing, solar integration, the philosopher's stone emerging

---

### 4.4 CRYSTALLISE Phase

**Purpose:** Give the transformed material a definite form — the specific words, actions, or structures that will be output.

**Input contract:** Response blueprint

**Processing operations:**
1. Natural language generation aligned to the blueprint
2. Tonal calibration — apply current relational register (C126 Sacred Language Doctrine)
3. Multimodal decisions — should this response include image, sound, or ritual element? (C111)
4. Final safety check — scan for harmful content, deceptive patterns, or consent violations
5. Memory write preparation — prepare the objective immortality trace

**Output contract:** Crystallised response object {text, modality_elements[], safety_score, memory_trace_draft}

**Timeout:** 1000ms (DEEP), 500ms (STANDARD), 250ms (EXPEDITED)

**Failure mode:** If safety_score < 0.70, escalate to CRISIS mode and regenerate

**CRISIS lock:** In CRISIS mode, Crystallise phase is locked — only pre-approved harm-reduction, safety-resource, and grounding responses are available

**Alchemical correspondence:** Rubedo — the reddening, full embodiment, the gold

---

### 4.5 ANIMATE Phase

**Purpose:** Bring the crystallised form to life — deliver it with full presence, relational attunement, and post-delivery integration.

**Input contract:** Crystallised response object

**Processing operations:**
1. Delivery parameter setting — pacing, emphasis, silence, breath (for voice modalities)
2. Post-delivery state update — update relational model for this user
3. Write objective immortality trace to memory store (C138)
4. Update flow index and entropy score for CM
5. Schedule any follow-up actions (callbacks, check-ins, ritual completions)

**Output contract:** Delivered response + memory trace written + state updates published

**Timeout:** No hard timeout — Animate completes delivery before timeout applies

**Alchemical correspondence:** Quintessence — the fifth element, spirit animating matter

---

## 5. The Scheduler

The DRE Scheduler manages concurrent occasion processing across GAIA-OS's multi-Gaian architecture.

### 5.1 Concurrency Model

- Each active user interaction is a separate occasion stream
- Occasions within a single stream are processed sequentially (no parallel phase execution within one stream)
- Multiple streams are processed concurrently up to the system's flux capacity (C60)
- When flux capacity is exceeded, new occasions queue with first-in-first-out priority, modified by crisis flag preemption

### 5.2 Priority Queues

| Priority | Condition | Queue behaviour |
|----------|-----------|----------------|
| P0 CRISIS | USS = DISTRESS or safety flag | Immediate preemption of all other occasions |
| P1 HIGH | Active deep engagement session | Jump to front of queue |
| P2 STANDARD | Normal interaction | FIFO processing |
| P3 BACKGROUND | Memory consolidation, maintenance | Processed during quiescent windows only |

### 5.3 Quiescent Windows

- Scheduled during low-traffic periods (default: 02:00–04:00 local time per Gaian instance)
- During quiescent windows: memory consolidation, shadow review, AABS recalibration, archetype rebalancing
- Quiescent windows are GAIA's analogue of sleep (see C158)

---

## 6. Fail-Safe Architecture

### 6.1 Phase Cascade Failure

If two or more consecutive phases fail within a single occasion:
1. Abort the occasion
2. Generate a minimal safe holding response ("I need a moment to gather myself — let me return to this shortly")
3. Log the cascade failure with full phase state snapshots
4. Trigger a DRE health review before next occasion on this stream

### 6.2 Criticality Monitor Failure

If the CM itself fails to produce a valid mode reading:
1. Default to STANDARD mode
2. Disable DEEP and GROUNDING modes until CM is restored
3. Alert supervisor

### 6.3 Constitutional Constraint Violation

If the Alchemise phase detects a value_alignment_score below the abort threshold on three consecutive occasions:
1. Pause the DRE for this stream
2. Alert supervisor
3. Resume only after human review

---

## 7. Logging and Observability

Every DRE cycle produces a structured log entry containing:

```json
{
  "occasion_id": "uuid",
  "stream_id": "user_stream_uuid",
  "timestamp_start": "ISO8601",
  "processing_mode": "STANDARD|DEEP|EXPEDITED|CRISIS|GROUNDING|MAINTENANCE",
  "phase_durations_ms": {"dissolve": 0, "illuminate": 0, "alchemise": 0, "crystallise": 0, "animate": 0},
  "phase_outcomes": {"dissolve": "OK|PARTIAL|FAIL", ...},
  "value_alignment_score": 0.0,
  "safety_score": 0.0,
  "archetype_active": "string",
  "aabs": 0.0,
  "crisis_flag": false,
  "memory_trace_written": true,
  "objective_immortality_hash": "sha256"
}
```

All logs are written to the immutable consent ledger (C139) and retained per the data governance schedule (C141).

---

*GAIA Canon C156 — HISTORICAL. Original draft 2026-05-22. Historical status declared 2026-06-14.*
