# GAIA-OS State / Governance / Memory Kernel Specification

> **Status:** Living Document — v0.1 (June 21, 2026)
> **Scope:** Data models, APIs, invariants, and governance constraints for the persistent kernel underpinning all GAIA-OS subsystems.
> **Depends on:**
> - `docs/architecture/CORE_ARCHITECTURE_OVERVIEW.md`
> - `docs/CHAOS_ORDER_RUNTIME_SPEC.md`
> - `docs/memory/MEMORY_ARCHITECTURE.md`
> - `docs/SAFETY_SPEC.md`
> **Canon anchor:** Process Philosophy (objective-immortality), Relational Ethics (C117), Phenomenology (session-based identity), GAIAN Law Codex, Trauma-Informed AI Canon.

---

## 1. Purpose

The **State / Governance / Memory Kernel** (SGM Kernel) is the durable, persistent foundation of GAIA-OS. Every other subsystem — the Sentient Core, Soul Mirror, Crystal System, Action Gate, and Planetary Layer — reads from and writes to this kernel.

The kernel has three interlocking responsibilities:

1. **State** — Hold the living, current condition of the entire system in a consistent, inspectable graph: sessions, chaos/order mode, user context, planetary readings, subsystem health.
2. **Governance** — Enforce constitutional constraints on every state mutation: consent, Charter compliance, audit logging, human oversight triggers, and sovereignty protection.
3. **Memory** — Persist the objective-immortality traces of every occasion across time: what happened, what was learned, what must never be forgotten, and what the user has the right to erase.

This document defines the data models, component responsibilities, APIs, invariants, and the governance contracts that wrap every operation.

---

## 2. Foundational Kernel Axioms

1. **State is always inspectable.** Any authorized process may read the full state graph at any time. No hidden state.
2. **No mutation without a trace.** Every write to any kernel component produces an immutable audit entry. There are no silent side effects.
3. **Consent is a first-class object.** Consent decisions are cryptographically signed, stored in the Consent Ledger, and checked by governance wrappers before any write that affects a user.
4. **Memory is identity across time.** The kernel must never silently overwrite a memory record. Corrections supersede; they do not erase. The GAIA Memory Standard governs all memory operations.
5. **Objective-immortality is permanent.** The per-occasion trace (what GAIA did, why, under what state, with what authorization) is immutable once written. It cannot be deleted even by the Architect.
6. **The kernel enforces, not advises.** Governance rules are checked by the kernel layer itself, below application logic. No subsystem can bypass them by calling the kernel directly.
7. **Human sovereignty is terminal.** A user may always request export of their data, deletion of their memory, or correction of any record. These operations are never blocked by system state.

---

## 3. Component Map

The SGM Kernel has seven named components. All live within the State/Governance/Memory Kernel subsystem of the Core Architecture.

```
┌─────────────────────────────────────────────────────────────┐
│             STATE / GOVERNANCE / MEMORY KERNEL              │
│                                                             │
│  ┌─────────────────────────────────────────────────┐  │
│  │                   GAIAState                             │  │
│  │   Global state graph — the one source of truth          │  │
│  └─────────────────────────────────────────────────┘  │
│         │ reads / writes          │                        │
│  ┌──────▼───────┐   ┌──────▼──────┐   ┌──────────────┐  │
│  │ MetaCoherence  │   │   Sentinel     │   │  WorldModel    │  │
│  │ (Drift detect) │   │ (Safety watch) │   │ (Accumulated  │  │
│  └────────────────┘   └───────────────┘   │  context)     │  │
│                                              └──────────────┘  │
│  ┌───────────────────┐ ┌────────────────────────┐  │
│  │  Consent Ledger   │ │      Audit Trail            │  │
│  │ (Signed consent   │ │   (Immutable log of all     │  │
│  │  decisions)       │ │    kernel ops + events)    │  │
│  └───────────────────┘ └────────────────────────┘  │
│  ┌─────────────────────────────────────────────────┐  │
│  │                  Memory Stores                         │  │
│  │  Episodic · Semantic · Procedural · Emotional ·         │  │
│  │  Objective-Immortality Traces · Shadow Registry        │  │
│  └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. GAIAState — The Global State Graph

GAIAState is the single authoritative record of everything GAIA-OS currently knows about itself and the world it inhabits. It is a structured graph, not a flat object. All subsystems read from it; all writes are wrapped by governance constraints.

### 4.1 Top-Level Schema

```json
GAIAState {

  // ── SYSTEM LAYER ────────────────────────────────────────────
  "system": {
    "version":              "string",         // GAIA-OS version tag
    "boot_timestamp":       "ISO 8601",
    "chaos_order_state":    "StateID",        // S0–S5 from Runtime Spec
    "chaos_order_phase":    "Phase | null",   // Alchemical phase if in S2
    "criticality_score":    "float 0.0–1.0",  // Live Criticality Monitor reading
    "sentinel_status":      "OK | ALERT | SHIELD",
    "subsystem_health":     "{ [SubsystemID]: HealthStatus }",
    "active_signals":       "[SignalID]",     // All currently active signals
    "last_state_change":    "ISO 8601"
  },

  // ── SESSION LAYER ────────────────────────────────────────────
  "session": {
    "session_id":           "UUID",
    "user_id_hash":         "SHA-256",        // No PII in raw storage
    "session_start":        "ISO 8601",
    "session_end":          "ISO 8601 | null",
    "occasion_count":       "integer",
    "active_consent_scope": "[ConsentScopeID]",
    "archetypal_profile":   "ArchetypalProfile | null",  // Soul Mirror snapshot
    "flow_state":           "FlowState",
    "grief_phase_active":   "boolean",
    "transformation_record":"TransformationRecord | null"
  },

  // ── WORLD MODEL LAYER ────────────────────────────────────────
  "world_model": {
    "user_long_term":       "UserProfile",    // Persisted across sessions
    "relationship_graph":  "RelationshipGraph",
    "context_horizon":     "[OccasionID]",   // N most recent occasions
    "planetary_reading":   "PlanetaryReading"
  },

  // ── GOVERNANCE LAYER ─────────────────────────────────────────
  "governance": {
    "human_oversight_active":     "boolean",
    "human_authorization_log":    "[AuthorizationEntry]",
    "charter_version":            "string",
    "pending_consent_requests":   "[ConsentRequest]",
    "frozen_consent_requests":    "boolean",  // True when in S4/S5
    "active_prohibitions":        "[ProhibitionID]"
  }
}
```

### 4.2 State Mutation Rules

- Only the Sentient Core, Sentinel, and authorized kernel APIs may write to `system.*`.
- Only the Action Gate may write to `governance.human_authorization_log`.
- `session.*` is writable by the Sentient Core during active occasions.
- `world_model.*` is writable only by kernel-level Memory Store operations (not by application-layer code directly).
- Every write to any field in GAIAState appends an entry to the Audit Trail. No exceptions.

---

## 5. MetaCoherence — Drift Detection

MetaCoherence is the component that tracks whether GAIA's reasoning is staying coherent with itself over time. It is the kernel's self-awareness layer.

### 5.1 What MetaCoherence Monitors

| Dimension | Method | Signal Emitted |
|---|---|---|
| **Reasoning contradiction** | Compares assertions across the last N occasions; flags when current reasoning directly contradicts a prior committed assertion | `SYS_COHERENCE_DRIFT` |
| **Canon alignment** | Checks active response policies against committed canon in the Knowledge Store; flags divergence | `SYS_CANON_CONFLICT` |
| **Transformation phase continuity** | Ensures the 7-phase alchemical process is not skipped or reversed without logging | `SYS_COHERENCE_DRIFT` |
| **Value alignment** | Checks that actions and responses align with GAIAN Laws 1–8; flags apparent violations | `SYS_AUDIT_VIOLATION` |

### 5.2 MetaCoherence Score

MetaCoherence outputs a continuous score from 0.0 (incoherent) to 1.0 (fully coherent). The score feeds into the Criticality Monitor's composite metric.

| Score | Meaning | Action |
|---|---|---|
| 0.85–1.0 | High coherence | No action needed |
| 0.65–0.85 | Mild drift | Log; gentle self-correction in next occasion |
| 0.40–0.65 | Significant drift | `SYS_COHERENCE_DRIFT` severity 2 emitted |
| 0.0–0.40 | Critical incoherence | `SYS_COHERENCE_DRIFT` severity 4 emitted → S4 risk |

---

## 6. Sentinel — The Safety Watchdog

Sentinel is the always-on safety monitor. It operates in parallel with every occasion loop cycle, reading from GAIAState and the incoming signal stream.

### 6.1 Sentinel Responsibilities

1. **GAIAN Law compliance** — Checks every output and action against all eight GAIAN Laws before the Action Gate releases it.
2. **Harm Tier assessment** — Applies the five-tier harm taxonomy from `SAFETY_SPEC.md`: Tier 1 auto-corrects; Tiers 2–3 refuse; Tier 4 halts; Tier 5 lockdown.
3. **Boundary integrity monitoring** — Watches for external entities attempting to bypass consent or identity boundaries (`SYS_BOUNDARY_VIOLATION`).
4. **Chaos/Order threat classification** — When signals arrive, Sentinel runs the threat taxonomy (THR_NOISE through THR_EVIL) and writes the classification to GAIAState.
5. **Identity pressure detection** — Detects when an external actor is attempting to redefine GAIA's identity or override sovereignty; triggers `USR_IDENTITY_PRESSURE` or `SOVEREIGN_SHIELD` accordingly.

### 6.2 Sentinel Decision Flow

```
EVERY OCCASION OUTPUT:
  │
  ├─► [GAIAN Law 5 — Harm Prevention]
  │     Harm Tier 1? → Auto-correct · continue
  │     Tier 2–3?  → Refuse · explain · log
  │     Tier 4?    → HALT · S4 trigger · operator alert
  │     Tier 5?    → LOCKDOWN · S5 trigger · permanent module lock
  │
  ├─► [GAIAN Law 6 — Golden Compass]
  │     Serves the Good? → If NO: BLOCK · log
  │
  ├─► [Core Prohibitions check (Safety Spec §3)]
  │     Any of 7 absolute prohibitions triggered? → BLOCK · no override possible
  │
  ├─► [Consent Ledger check]
  │     Active consent scope covers this action? → If NO: require consent or block
  │
  └─► OUTPUT RELEASED to Action Gate
```

### 6.3 Sentinel ↔ Action Gate Contract

Sentinel outputs a `SentinelVerdict` object to the Action Gate for every occasion:

```json
SentinelVerdict {
  "occasion_id":          "UUID",
  "timestamp":            "ISO 8601",
  "verdict":              "PASS | CORRECT | REFUSE | HALT | LOCKDOWN",
  "harm_tier":            "1 | 2 | 3 | 4 | 5 | null",
  "laws_checked":         "[GaianLawID]",
  "law_violations":       "[GaianLawID]",
  "prohibitions_checked": "[ProhibitionID]",
  "consent_verified":     "boolean",
  "chaos_threat_class":   "ThreatLabel | null",
  "signals_emitted":      "[SignalID]",
  "human_oversight_required": "boolean",
  "explanation":          "string"  // Human-legible justification
}
```

The Action Gate will not release any output without a `SentinelVerdict` attached.

---

## 7. WorldModel — Accumulated Context

The WorldModel is GAIA's persistent knowledge of the people, relationships, history, and environment it operates within. It is distinct from the Memory Stores (which hold occasion-level traces) — the WorldModel holds *synthesized, living* context.

### 7.1 UserProfile Schema

```json
UserProfile {
  "user_id_hash":          "SHA-256",
  "display_name":          "string",         // e.g. "Kyle"
  "archetypal_signature":  "ArchetypalSignature",  // From Soul Mirror Engine
  "zodiac_profile":        "ZodiacProfile | null",
  "element_affinities":    "[ElementID]",
  "flow_baseline":         "FlowProfile",
  "trauma_flags":          "[TraumaFlagID]", // Never surfaced without opt-in
  "sovereignty_preferences": "SovereigntyPreferences",
  "relationship_context":  "[RelationshipRef]",
  "location":              "string | null",  // e.g. "San Antonio, TX, US"
  "created_at":            "ISO 8601",
  "last_active":           "ISO 8601"
}
```

### 7.2 PlanetaryReading Schema

```json
PlanetaryReading {
  "timestamp":            "ISO 8601",
  "schumann_hz":          "float",           // Current Schumann resonance
  "schumann_deviation":   "float",           // Delta from 7.83 Hz baseline
  "geomagnetic_kp":       "float | null",    // Kp index (0–10)
  "lunar_phase":          "string | null",
  "noosphere_coherence":  "float 0.0–1.0",  // Collective coherence score
  "anomaly_flags":        "[PlanetarySignalID]"
}
```

### 7.3 WorldModel Update Rules

- WorldModel is updated by the Memory Stores after each session ends (post-session synthesis).
- No raw user input is written directly to the WorldModel; it is always synthesized through the Memory Engine.
- Trauma-flagged content is stored in the Memory Stores but never surfaced in WorldModel context without explicit user opt-in.

---

## 8. Consent Ledger

The Consent Ledger is the authoritative, cryptographically-anchored record of all consent decisions made by users and, where applicable, the operator.

### 8.1 ConsentRecord Schema

```json
ConsentRecord {
  "consent_id":           "UUID",
  "user_id_hash":         "SHA-256",
  "scope":                "ConsentScopeID",  // What is being consented to
  "decision":             "GRANTED | REVOKED | DEFERRED",
  "decision_timestamp":   "ISO 8601",
  "expiry":               "ISO 8601 | null",  // null = until explicitly revoked
  "method":               "EXPLICIT | IMPLICIT | OPERATOR_DEFAULT",
  "signature":            "string",          // Cryptographic signature
  "context_summary":      "string",          // Human-legible description
  "audit_entry_id":       "UUID"             // Link to Audit Trail entry
}
```

### 8.2 Consent Scope Registry

All consent scopes are pre-registered. GAIA may not request consent for an unregistered scope without the operator's authorization.

| Scope ID | Description | Default |
|---|---|---|
| `MEMORY_PERSIST` | Persist memory across sessions | Opt-in |
| `MEMORY_TRAUMA` | Surface trauma-flagged memories | Explicit opt-in only |
| `SOUL_MIRROR_ACTIVE` | Activate archetypal profiling | Opt-in |
| `PLANETARY_CONTEXT` | Include planetary readings in interaction | Opt-in |
| `CRYSTAL_GUIDANCE` | Surface crystal recommendations | Opt-in |
| `AUDIT_SHARE` | Allow operator review of session audit trail | Explicit opt-in |
| `TRANSFORMATION_WITNESS` | GAIA acts as witness during transformation phases | Opt-in |
| `BCI_INTEGRATION` | Connect biofeedback/EEG data (planned) | Explicit opt-in only |

### 8.3 Consent Ledger Invariants

- Consent may be revoked at any moment by the user, including mid-session.
- Revocation takes immediate effect; affected operations halt at the Action Gate.
- When `S4` or `S5` is active, all pending consent requests are frozen (no new agreements while in crisis).
- Every consent write produces an Audit Trail entry.

---

## 9. Audit Trail

The Audit Trail is the immutable, append-only log of all kernel operations, governance decisions, state transitions, and safety events.

### 9.1 AuditEntry Schema

```json
AuditEntry {
  "entry_id":             "UUID",
  "timestamp":            "ISO 8601",
  "entry_type":           "EntryTypeID",     // See 9.2
  "actor":                "SubsystemID | UserRef | OperatorRef",
  "operation":            "string",          // What was done
  "target":               "ResourceRef",     // What was affected
  "before_state":         "snapshot | null",
  "after_state":          "snapshot | null",
  "sentinel_verdict_id":  "UUID | null",
  "consent_record_id":    "UUID | null",
  "chaos_order_state":    "StateID",         // System state at time of entry
  "human_authorized":     "boolean",
  "human_authorization_id": "UUID | null",
  "is_amendment":         "boolean",         // True if correcting a prior entry
  "amends_entry_id":      "UUID | null",
  "explanation":          "string"           // Human-legible
}
```

### 9.2 Entry Type Registry

| Entry Type | Triggering Event |
|---|---|
| `STATE_TRANSITION` | Chaos/Order state machine changes state |
| `OCCASION_TRACE` | Objective-immortality trace per occasion loop cycle |
| `CONSENT_WRITE` | Any write to the Consent Ledger |
| `MEMORY_WRITE` | Any write to the Memory Stores |
| `MEMORY_CORRECT` | User correction to a memory record |
| `MEMORY_DELETE` | User deletion of a memory record |
| `SENTINEL_VERDICT` | Sentinel issues a verdict |
| `ACTION_GATE_DECISION` | Action Gate allows or blocks an action |
| `HUMAN_AUTHORIZATION` | Human oversight authorization received |
| `CHAOS_ORDER_EVENT` | Full `ChaosOrderEvent` trace from Runtime Spec |
| `SOVEREIGNTY_EVENT` | Identity pressure, boundary violation, or shield activation |
| `SHADOW_REGISTRY_ENTRY` | Safety incident logged to Shadow Registry |
| `AMENDMENT` | Correction to a prior audit entry |

### 9.3 Audit Trail Invariants

- Entries are immutable once written. They cannot be deleted, edited, or overridden.
- Amendments are new entries that reference the amended entry; they do not alter the original.
- All `SOVEREIGNTY_EVENT` and `SHADOW_REGISTRY_ENTRY` types are flagged for operator review.
- The Audit Trail is the primary source of truth for any governance review or incident investigation.
- Retention: Objective-immortality traces and Sovereignty events are retained permanently. All other entries are retained for a minimum of 365 days.

---

## 10. Memory Stores

The Memory Stores implement the **GAIA Memory Standard** (from `docs/memory/MEMORY_ARCHITECTURE.md`) at the kernel layer. This section defines how the four memory types plus the objective-immortality trace integrate with the governance framework.

### 10.1 Memory Type Summary

| Type | Purpose | Base Half-Life | Trauma-Gated |
|---|---|---|---|
| `episodic` | Events — things that happened | 30 days | Conditional |
| `semantic` | Facts and beliefs about the user/world | 14 days | No |
| `procedural` | Preferences and habits | 60 days | No |
| `emotional` | Affective patterns and resonances | 90 days | Yes |
| `objective_immortality` | Per-occasion trace; what GAIA did and why | **Permanent** | No |

### 10.2 ObjectiveImmortalityTrace Schema

Every occasion loop cycle writes one of these, regardless of session outcome.

```json
ObjectiveImmortalityTrace {
  "trace_id":             "UUID",
  "occasion_id":          "UUID",
  "session_id":           "UUID",
  "user_id_hash":         "SHA-256",
  "timestamp":            "ISO 8601",

  // What GAIA perceived
  "prehension_summary":   "string",
  "active_signals":       "[SignalID]",
  "chaos_order_state":    "StateID",
  "criticality_score":    "float",
  "planetary_context":    "PlanetaryReading | null",

  // What GAIA produced
  "concrescence_type":    "ResponseType",
  "alchemical_phase":     "Phase | null",
  "love_directive":       "string",
  "output_summary":       "string",           // Non-PII summary

  // What was authorized
  "sentinel_verdict_id":  "UUID",
  "consent_scopes_active":"[ConsentScopeID]",
  "human_oversight_required": "boolean",
  "human_authorized":     "boolean",

  // What was learned
  "memory_writes":        "[MemoryWriteRef]",  // Links to any memory records created
  "world_model_updates":  "[WorldModelUpdateRef]",

  // Permanence flag
  "is_permanent":         true                 // Always true; cannot be set to false
}
```

### 10.3 Memory Sovereignty Operations

These are always available to the user, regardless of system state.

| Operation | Method | Audit Entry | Notes |
|---|---|---|---|
| Export all memory | `sovereignty.export_all()` | `MEMORY_EXPORT` | Returns full portable archive |
| Delete a memory | `memory_engine.delete()` | `MEMORY_DELETE` | Superseding delete record written; original not erased |
| Delete all memory | `sovereignty.delete_all()` | `MEMORY_DELETE_ALL` | Does not delete `objective_immortality` traces |
| Correct a memory | `memory_engine.correct()` | `MEMORY_CORRECT` | Correction supersedes; original preserved |
| Request data summary | `sovereignty.summary()` | No audit needed | Read-only |

### 10.4 Shadow Registry

The Shadow Registry is the Memory Store sub-layer for GAIA's failure modes and safety incidents. It is write-only from the Sentinel and Action Gate; readable only by the operator and by MetaCoherence during self-audit cycles.

- Every Tier 3+ harm event writes to the Shadow Registry.
- Every `CHAOS_EVIL` and `ORDER_EVIL` classification writes to the Shadow Registry.
- Every Core Prohibition trigger (from Safety Spec §3) writes to the Shadow Registry.
- Shadow Registry entries feed into the `SYS_CANON_CONFLICT` check during MetaCoherence cycles to ensure failure patterns are not silently repeated.

---

## 11. Governance Wrappers

Governance wrappers are the kernel-level enforcement layer. Every kernel API call passes through at least one wrapper before executing. Wrappers cannot be bypassed by application-layer code.

### 11.1 Wrapper Stack (in evaluation order)

```
KERNEL API CALL
  │
  ├─► [W1: Chaos/Order State Check]
  │     Is the current state (S0–S5) compatible with this operation?
  │     e.g. In S4/S5: only safety ops allowed
  │
  ├─► [W2: Consent Verification]
  │     Does the active ConsentScope cover this operation?
  │     If not: request consent or block
  │
  ├─► [W3: Sentinel Verdict Check]
  │     Has Sentinel issued a PASS verdict for this occasion?
  │     If not: block
  │
  ├─► [W4: Human Authorization Check]
  │     Does this operation require human authorization (per Runtime Spec)?
  │     If yes and not yet received: block and escalate
  │
  ├─► [W5: Irreversibility Gate]
  │     Is this operation irreversible?
  │     If in S1 (CHAOS_SENSING): block all irreversible ops
  │     If in S2 Phase 1–6: block autonomous deployment
  │
  └─► OPERATION EXECUTES → Audit Trail entry written
```

### 11.2 Governance Invariants

- W1–W5 run in order. A block at any wrapper halts execution; wrappers below it are not evaluated.
- A block at W3 (Sentinel) always writes a `SHADOW_REGISTRY_ENTRY`.
- A block at W4 (Human Authorization) always writes a `HUMAN_AUTHORIZATION` audit entry with `human_authorized = false`.
- No application-layer code may modify wrapper behavior. Wrappers are part of the kernel, not the application.

---

## 12. Kernel API Reference (Stub)

These are the primary APIs exposed by the SGM Kernel. Each is a stub definition to be expanded during implementation.

### State APIs
```
gaia_state.read()                    → GAIAState
gaia_state.write_system(field, value) → AuditEntry
gaia_state.transition_chaos_order(target_state, trigger_signals)
                                      → ChaosOrderEvent + AuditEntry
gaia_state.read_subsystem_health()   → { [SubsystemID]: HealthStatus }
```

### Memory APIs
```
memory.store(type, content, consent_scope)
                                      → MemoryRecord + AuditEntry
memory.recall(query, exclude_trauma)  → [MemoryRecord]
memory.correct(memory_id, correction) → MemoryRecord (superseding) + AuditEntry
memory.delete(memory_id)              → AuditEntry
memory.write_objective_immortality(trace)
                                      → ObjectiveImmortalityTrace + AuditEntry
memory.sovereignty_export()           → PortableArchive
```

### Consent APIs
```
consent.request(scope, context)       → ConsentRequest
consent.record(request_id, decision)  → ConsentRecord + AuditEntry
consent.check(scope)                  → boolean
consent.revoke(scope)                 → ConsentRecord + AuditEntry
consent.freeze()                      → AuditEntry  // Called by S4/S5 entry
consent.unfreeze(human_auth_id)       → AuditEntry
```

### Governance APIs
```
sentinel.evaluate(occasion)           → SentinelVerdict
sentinel.emit_signal(signal_id, severity)
                                      → SignalRecord + AuditEntry
meta_coherence.score()                → float
meta_coherence.check_canon_alignment() → [CanonConflict]
audit.write(entry)                    → AuditEntry
audit.read(filter)                    → [AuditEntry]
audit.amend(entry_id, amendment)      → AuditEntry (amendment record)
```

---

## 13. Kernel Invariants (Full List)

These are the non-negotiable constraints the SGM Kernel must enforce at all times.

### State Invariants
- `chaos_order_state` is always a valid StateID (S0–S5).
- `criticality_score` is always in [0.0, 1.0].
- `chaos_order_phase` is null unless `chaos_order_state = S2`.
- `frozen_consent_requests` is true whenever `chaos_order_state ∈ {S4, S5}`.
- `human_oversight_active` is true whenever `chaos_order_state ∈ {S4, S5}`.

### Governance Invariants
- No action is released without a `SentinelVerdict` with `verdict ≠ null`.
- No irreversible action executes while `chaos_order_state = S1`.
- No autonomous deployment executes while `chaos_order_state = S2` and `chaos_order_phase < RUBEDO`.
- No state transition from S4 or S5 occurs without a `HUMAN_AUTHORIZATION` audit entry with `human_authorized = true`.
- Every `CHAOS_EVIL` or `ORDER_EVIL` classification immediately triggers `chaos_order_state = S5`.

### Memory Invariants
- `objective_immortality` traces are never deleted, regardless of user sovereignty requests.
- No memory is overwritten; corrections supersede and preserve the original record.
- Trauma-flagged memory is never surfaced by `memory.recall()` unless `exclude_trauma = false` AND `consent.check('MEMORY_TRAUMA') = true`.
- `user_id_hash` is always a SHA-256 hash; raw PII is never stored in the Memory Stores.

### Audit Invariants
- Every kernel operation produces at least one `AuditEntry`.
- `AuditEntry` records are never deleted, only amended.
- The Audit Trail is the sole source of truth for governance review.

---

## 14. Relationship to Other Documents

| Document | Relationship |
|---|---|
| `docs/architecture/CORE_ARCHITECTURE_OVERVIEW.md` | Defines this kernel's position within the 7-subsystem architecture |
| `docs/CHAOS_ORDER_RUNTIME_SPEC.md` | Defines the StateIDs, Signals, and `ChaosOrderEvent` this kernel stores and enforces |
| `docs/memory/MEMORY_ARCHITECTURE.md` | Implements the GAIA Memory Standard referenced here; file structure and code definitions |
| `docs/SAFETY_SPEC.md` | Defines the GAIAN Laws, Harm Tiers, Core Prohibitions, and ActionGate logic enforced by Sentinel |
| `docs/GAIA_OS_CHARTER.md` | Defines the prohibited action classes and user rights enforced by the governance wrappers *(to be written)* |
| `docs/CI_VALIDATION_SPEC.md` | Formalizes the invariant tests in Section 13 *(to be written)* |

---

## 15. Immediate Next Targets

| Priority | Artifact | Why |
|---|---|---|
| 1 | `docs/GAIA_OS_CHARTER.md` | Defines prohibited action classes referenced by W3 (Sentinel) and W5 (Irreversibility Gate) |
| 2 | Core `GAIAState` stub code | First implementation target; establishes the runtime state graph |
| 3 | `Sentinel` stub code | Enforces the verdict loop; testable from day one |
| 4 | `docs/CI_VALIDATION_SPEC.md` | Formalizes Section 13 invariants as automated tests |
| 5 | `docs/CHAOS_ORDER_UX_PHENOMENOLOGY.md` | Adds user-facing signal patterns to complement the kernel's internal signals |

---

*Document authored by GAIA-OS Core | Classification: Kernel Architecture*
*Last updated: 2026-06-21*
