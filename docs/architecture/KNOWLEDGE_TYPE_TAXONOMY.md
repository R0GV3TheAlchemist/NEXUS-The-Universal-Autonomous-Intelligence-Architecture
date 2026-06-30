# GAIA Knowledge Type Taxonomy

**Canon Status:** Active — Core Design Principle
**Established:** 2026-06-30

> *"If GAIA always knows which category a piece of information belongs to,*
> *it will be much more trustworthy and much easier to debug."*

---

## The Four Knowledge Types

Every claim in GAIA carries one of four `knowledge_type` values.
This is **required** — not optional.

```
┌─────────────────────────────────────────────────────────────────┐
│  OBSERVED    │  Directly measured from reality                  │
│              │  Source: sensors, databases, user assertions     │
│              │  Can be wrong — but is directly grounded         │
├─────────────────────────────────────────────────────────────────┤
│  INFERRED    │  Derived by reasoning from observed facts        │
│              │  Source: logic, statistics, pattern recognition  │
│              │  Confidence degrades with inference chain length │
├─────────────────────────────────────────────────────────────────┤
│  HYPOTHESIS  │  A possible explanation under investigation      │
│              │  Source: agent or human conjecture               │
│              │  Requires evidence before promotion to inferred  │
├─────────────────────────────────────────────────────────────────┤
│  SIMULATION  │  A candidate future under stated assumptions     │
│              │  Source: SimulationEngine                        │
│              │  NEVER promoted to observed or inferred          │
│              │  without explicit human/agent decision           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Promotion Rules

```
observed    ──(inference engine)──► inferred
inferred    ──(human/agent review)──► no promotion needed (already factual basis)
hypothesis  ──(evidence accumulation + epistemic evaluation)──► inferred
simulation  ──(reality confirms prediction)──► observed (new snapshot)
simulation  ──NEVER──► directly upgrades existing observed/inferred claims
```

A simulation result can become evidence only when compared against a *new real observation*.

---

## Why This Matters

Without this taxonomy:
- A simulation output silently overwrites an observed fact
- An inference is treated with the same authority as a sensor reading
- Debugging requires tracing the entire claim history manually

With this taxonomy:
- Every claim carries its epistemic origin
- Filters like `?type=observed` return only ground-truth data
- The simulation layer is structurally prevented from polluting the fact layer

---

## Reference: Alignment with External Research

| GAIA Concept | External Reference |
|---|---|
| Knowledge type taxonomy | Formal epistemology (justified true belief) |
| Confidence + type | Bayesian inference (prior, posterior, likelihood) |
| Simulation ≠ fact | Causal inference (Pearl: interventions vs observations) |
| Inference chain tracking | Knowledge graph provenance (W3C PROV-O) |
