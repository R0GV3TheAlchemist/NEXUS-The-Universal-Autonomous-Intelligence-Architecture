# GAIA Temporal World Model Layer — v0.3

**Canon Status:** Active — Engineering
**Established:** 2026-06-30
**Layer:** World Model — Temporal Versioning

> *"Without temporal layer: GAIA = memory system.*
> *With temporal layer: GAIA = evolving reality model.*
> *That is the difference between a knowledge base and a world model."*

---

## What This Layer Adds

GAIA already knew:
- **What exists** — Ontology Layer
- **What is true** — Epistemic Layer
- **Why it happens** — Causal Layer (v0.4)

Now GAIA knows:
- **When things happen**
- **How reality changes over time**
- **What GAIA believed at any prior moment**

---

## Core Components

### WorldSnapshot
A frozen, immutable version of GAIA's world state at a specific moment.

In the 'Git for reality' metaphor:
```
snapshot   = git commit
state      = full repo contents at that commit  
timestamp  = commit timestamp
trigger    = commit message
```

### TemporalEngine
Maintains the full ordered history of WorldSnapshots.
Append-only — truth states are never silently overwritten (GAIAN_LAW L3).

Key queries:
```python
# What did GAIA believe at time T?
engine.get_at_time(timestamp)

# What changed between two moments?
engine.diff(snapshot_a, snapshot_b)

# How has a specific claim's confidence evolved?
engine.belief_drift(claim_id)

# Which claims have flipped epistemic status over time?
engine.detect_temporal_contradictions()
```

---

## New Power Unlocked: Temporal Contradiction Resolution

Before the temporal layer, GAIA could only detect synchronic contradictions:
> *"These two claims conflict right now."*

With the temporal layer, GAIA can distinguish:

| Type | Example | Resolution |
|---|---|---|
| True contradiction | Two claims with opposite status at the same time | Flag for human review |
| Temporal state change | Claim was supported at T1, disputed at T2 | No contradiction — reality evolved |
| Belief drift | Confidence declined from 0.8 → 0.4 over 6 months | Track + surface |

This is how GAIA avoids treating evolution as error.
Time-indexed truth is not contradiction. It is growth.

---

## The Complete GAIA Stack (v0.3)

| Layer | Module | What It Knows |
|---|---|---|
| Ontology | `gaia/ontology/` | What exists |
| Epistemics | `gaia/epistemics/` | What is true + confidence |
| Contradiction | `gaia/contradiction/` | What conflicts |
| **Temporal** | **`gaia/world/temporal.py`** | **When + how reality evolves** |
| Causal | `gaia/causal/` (v0.4) | Why things happen |
| Agents | `gaia/agents/` (v0.5) | What acts on world state |

---

*© 2026 Kyle Steen — All rights reserved.*
