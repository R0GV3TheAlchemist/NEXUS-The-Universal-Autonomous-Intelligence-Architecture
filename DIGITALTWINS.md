# DIGITAL TWINS

**NEXUS — The Universal Autonomous Intelligence Architecture**
Copyright (c) 2026 R0GV3 The Alchemist

---

## Overview

NEXUS Digital Twins are **living, synchronised representations**
of physical entities, GAIA nodes, environments, and beings.
They enable GAIA to model, predict, and interact with the
physical world without requiring continuous physical contact,
and to maintain **consent-governed access** to the data they
represent.

The architecture draws from:
- **Azure Digital Twins** — twin graph and DTDL model definitions
- **Eclipse Ditto** — state channels and twin sync protocol
- **W3C Web of Things (WoT)** — semantic descriptions, consent, and provenance
- **GAIAN_LAWS.md Law II** — Right to Forget (consent-driven deletion)

---

## Core Concepts

### TwinSpec

A `TwinSpec` is the **immutable descriptor** for a digital twin:
its identity, model reference, owner, and initial properties.
Once created, a TwinSpec's `twin_id` is permanent. Properties
can change; identity cannot.

### TwinState

`TwinState` represents the **current state snapshot** of a twin:
current property values, lifecycle status, and last sync timestamp.
State is mutable and versioned — every update produces a new
state record that can be traced back to a physical event.

### SyncPlan

A `SyncPlan` defines **how** a twin stays in sync with its
physical counterpart:

| Strategy | Description |
|----------|-------------|
| `push` | Physical entity pushes state to twin on change |
| `pull` | Twin periodically polls physical entity |
| `bidirectional` | Two-way sync with conflict resolution policy |

Conflict resolution policies:
- `physical-wins` — physical world is ground truth (default)
- `twin-wins` — twin state is authoritative (controlled environments)
- `merge` — field-level merge with human-review on conflict

### TwinConsent

Every access to twin data requires a `TwinConsent` record.
Consent governs who can read, write, sync, or delete a twin's
data. Consent has an optional expiry and can be revoked at any
time, triggering automatic data quarantine per **GAIAN_LAWS.md
Law II — Right to Forget**.

Consent permissions:
- `read` — observe current state
- `write` — update twin properties
- `sync` — execute SyncPlan
- `delete` — permanently remove twin data

---

## Consent & Provenance Architecture

```
 TwinOrchestrator
       |
  ┌────┴────────────────────┐
  │  TwinConsent Registry   │
  │  (grant / revoke / ttl) │
  └────┬────────────────────┘
       │
  ┌────▼────────────────────┐
  │  Provenance Log         │
  │  (Merkle-DAG, immutable)│
  └─────────────────────────┘
```

Every state mutation is logged to an **immutable provenance
chain** (Merkle-DAG). Consent revocation triggers:
1. Immediate suspension of all active sync operations
2. Quarantine of twin data (read-only, access-logged)
3. Scheduled deletion per configurable retention policy
4. Provenance record of the revocation event

---

## GAIA Integration Points

| GAIA Module | Twin Role |
|-------------|-----------|
| `twins` | Core orchestration — TwinSpec, TwinState, SyncPlan, TwinConsent |
| `sovereignmemory` | Stores twin provenance chain segments |
| `governance` | Enforces consent policies via GovernanceEngine |
| `timeservice` | Timestamps all sync events with authoritative time |
| `resilience` | Monitors TwinOrchestrator health; restarts on failure |
| `mesh` | Distributes twin state updates across GAIA nodes |

---

## DTDL Model Reference

Twin models are described using **Digital Twin Definition Language
(DTDL v3)**, compatible with Azure Digital Twins. Model files
are stored under `specs/dtdl/` (Phase E).

Example model (GAIA Node Twin):
```json
{
  "@context": "dtmi:dtdl:context;3",
  "@id": "dtmi:gaia:node;1",
  "@type": "Interface",
  "displayName": "GAIA Node",
  "contents": [
    { "@type": "Property", "name": "stage", "schema": "string" },
    { "@type": "Property", "name": "health", "schema": "string" },
    { "@type": "Telemetry", "name": "affect_valence", "schema": "double" }
  ]
}
```

---

## Implementation Roadmap

| Phase | Deliverable |
|-------|-------------|
| C | `twins` module stubs (TwinSpec, TwinState, SyncPlan, TwinConsent, TwinOrchestrator) |
| D | This document; DTDL model directory structure |
| E | TwinOrchestrator.sync() implementation; provenance Merkle-DAG |
| F | Eclipse Ditto REST API integration; W3C WoT semantic descriptions |
| G | Azure Digital Twins graph integration; live bidirectional sync |

---

## References

- [Azure Digital Twins — DTDL v3](https://learn.microsoft.com/en-us/azure/digital-twins/concepts-models)
- [Eclipse Ditto — Open Source Digital Twins](https://eclipse.dev/ditto/)
- [W3C Web of Things — Thing Description](https://www.w3.org/TR/wot-thing-description/)
- [Portable Agent Memory Protocol (arXiv 2605.11032)](https://arxiv.org/abs/2605.11032)
- [GAIAN_LAWS.md — Law II: Right to Forget](GAIAN_LAWS.md)

---

## Version History

| Version | Date | Notes |
|---------|------|-------|
| 1.0 | 2026-07-22 | Initial NEXUS Digital Twins specification |

---

*"A twin is not a copy. It is a promise to pay attention."*
*— R0GV3 The Alchemist*
