# ADR-001 — Knowledge Type Taxonomy

**Status:** Accepted
**Date:** 2026-06-30
**Author:** GAIA Core

---

## Problem

GAIA handles information from multiple epistemic sources: sensor readings, user assertions,
logical inferences, probabilistic conclusions, and hypothetical simulations.
Without a formal taxonomy, all of these collapse into a single undifferentiated "claim,"
making the system untrustworthy and nearly impossible to debug.

## Decision

Every piece of knowledge in GAIA carries an explicit `knowledge_type` field:

| Type | Definition | Example |
|---|---|---|
| `observed` | Directly sensed or measured from reality | Sensor reading, database record, user-submitted fact |
| `inferred` | Derived by logical or statistical reasoning | "Energy demand is rising" (from usage trends) |
| `hypothesis` | A possible explanation under investigation | "Renewable shift may reduce costs" |
| `simulation` | A candidate future under stated assumptions | Output of `SimulationEngine.run()` |

This field is **required** on every Claim object. Claims without a type are rejected at ingestion.

## Alternatives Considered

| Alternative | Why rejected |
|---|---|
| Single confidence score only | Confidence does not encode epistemic origin — a high-confidence simulation is still not an observation |
| Optional type field | Optional fields become absent fields; ambiguity defeats the purpose |
| Free-text provenance string | Unstructured; not queryable or enforceable |

## Consequences

**Gains:**
- Every consumer of GAIA data knows exactly what kind of knowledge it is looking at
- Simulations can never be silently promoted to facts
- Debugging is vastly simpler: filter by type to isolate observed vs inferred state
- Aligns with formal epistemology (justified true belief requires distinguishing source)

**Losses / Trade-offs:**
- All existing claim ingestion code must be updated to include this field
- External data sources require a mapping step to assign types

**Follow-on work:**
- Issue: Enforce `knowledge_type` at API boundary validation layer
- Issue: Build type-aware query filters on `/state` endpoint
- ADR-002: Evidence traceability (how claims link back to their source)
