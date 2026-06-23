# GAIA Simulation Schema

> *"A simulation that cannot be falsified is a belief. A belief that cannot be built is a dream. Document the gap between them."*

---

## Purpose

This document defines the **documentation contract** for every simulation in the GAIA-OS simulation layer. It exists because:

1. Code encodes *what* is modeled. Documentation encodes *why* the model was built that way.
2. Without proof documents, the reasoning behind schema decisions lives only in the author's head and is lost between sessions.
3. GAIA-OS is a cumulative system. Each sim should be legible to future contributors, collaborators, and to GAIA herself — not just to the person who wrote it.

This schema is the minimum standard. Every sim is required to meet it before its status is moved from **Open** to **Confirmed**, **Partial**, or **Falsified** in `simulation/README.md`.

---

## The Three Required Artifacts

### 1. The Sim File — `simulation/<name>_sim.py`

The executable specification. The formal model in code.

**Required elements:**

```python
"""
<name>_sim.py

Hypothesis:
    One to three sentences. What does this simulation claim is true?
    The claim must be falsifiable — it must be possible for the simulation to
    return results that do NOT support it.

Schema Overview:
    What entities does the sim define? What are the key parameters?
    Why were those parameters chosen over alternatives?

Output:
    What files does the sim write? Where?
    What columns/fields do they contain?

Canon References:
    Which canon documents (e.g. C00, C35, C44) ground this simulation?

Author: R0GV3TheAlchemist
Date: YYYY-MM-DD
"""
```

**Code standards:**
- Use `@dataclass` for all entities (ColorAtom, FieldNode, GovernanceAgent, etc.)
- All parameters that affect results must be defined as named constants at the top of the file, not hardcoded inline
- The `main()` function must write output to `simulation/output/` — never print-only
- The sim must be runnable standalone: `python -m simulation.<name>_sim`
- Include a brief `if __name__ == "__main__": main()` block

---

### 2. The Proof Document — `proofs/<NAME>_PROOF.md`

The scientific record. The permanent account of what was hypothesized, what was built, and what was learned.

**Required sections:**

```markdown
# <Sim Name> Proof

## Hypothesis
Restate the hypothesis verbatim from the sim file docstring.
This is the claim being tested.

## Schema Design Decisions
For each non-obvious design choice in the sim, document:
- What was chosen
- What alternatives were considered
- Why this choice was made

This is the most important section. Schema decisions are where the
intuition of the builder is encoded. Without this, the next person
(or a future GAIA session) cannot understand why the model behaves
the way it does.

## Simulation Parameters
List all named constants and their values at time of the confirmed run.
This ensures results can be reproduced.

| Parameter | Value | Rationale |
|---|---|---|
| WEIGHT_COMPLEMENTARITY | 0.5 | Primary driver — angular distance is the strongest predictor |
| WEIGHT_CHARGE | 0.3 | Secondary — charge opposition contributes but doesn't dominate |
| WEIGHT_RESONANCE | 0.2 | Tertiary — amplitude matters but not as much as structure |

## Results
Summarize the key output data. Include:
- The central finding (the number or distribution that answers the hypothesis)
- Any surprising or anomalous results
- What the baseline comparison showed (if applicable)

Do not paste raw CSV here — summarize the signal.

## Conclusion
Did the simulation support the hypothesis? Options:
- **Confirmed** — data supports the hypothesis as stated
- **Partial** — hypothesis supported in some conditions but not others; specify
- **Falsified** — data does not support the hypothesis; state what was found instead

## Implications for GAIA
What does this result mean for the rest of the system?
- Which other sims does this inform or constrain?
- Does this change how any canon document should be interpreted?
- What new hypotheses does this open?

## Open Questions
What this sim did not resolve. What the next sim in this domain should test.

## Date Filed
YYYY-MM-DD
```

---

### 3. The Output Data — `simulation/output/<name>_results.csv`

The falsifiable record. The actual numbers.

**Requirements:**
- Written by the sim file, never manually created or edited
- Column headers must be self-describing (e.g. `coherence_score`, not `cs` or `val3`)
- Must include enough columns to reproduce the key finding without re-running the sim
- Companion markdown report (`<name>_report.md`) is encouraged but not required

---

## Status Definitions

Used in `simulation/README.md` index:

| Status | Meaning | Required to assign |
|---|---|---|
| **Open** | Sim file exists; proof doc not yet filed | Default for all new sims |
| **Confirmed** | Hypothesis supported by output data | All 3 artifacts present; proof doc filed |
| **Partial** | Hypothesis partially supported | All 3 artifacts present; partial conclusion documented |
| **Falsified** | Hypothesis not supported | All 3 artifacts present; canon revision noted |
| **Support file** | Visualization or utility companion; no independent hypothesis | Noted in index |

---

## Closing Open Sims

As of June 23, 2026, 16 of 17 sims are Open. The priority order for closing them is:

1. **`canon_law_sim.py`** (28KB) — largest sim; governance hypothesis is load-bearing for GAIA architecture
2. **`chaos_order_runtime_sim.py`** (26KB) — runtime stability hypothesis affects all other sims
3. **`quantum_chemistry_sim.py`** (23KB) — foundational physics layer; C43 grounding
4. **`alignment_enforcement_sim.py`** (16KB) — C35 alignment; directly affects Sovereign Axiology
5. **`cosmological_field_sim.py`** (16KB) — C00/C41 coherence field structure
6. Remaining sims in descending file size order

For each: run the sim, review output, file the proof document, update status in `README.md`.

---

## Reference: Completed Proof

See `proofs/COLOR_ATOMIZATION_PROOF.md` as the canonical example of a correctly filed proof document.

---

**R0GV3TheAlchemist — June 23, 2026**
