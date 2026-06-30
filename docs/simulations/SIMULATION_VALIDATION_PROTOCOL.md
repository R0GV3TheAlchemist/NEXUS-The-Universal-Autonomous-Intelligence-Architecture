# SIMULATION VALIDATION PROTOCOL
## Three-Pass Discovery → Refinement → Verification Standard

**Status:** CANONICAL  
**Version:** 1.0  
**Established:** 2026-06-30  
**Established by:** R0GV3 (Kyle Steen, Seat I — The Coherence Council)  
**Phase:** G-15 — The Rhythm Phase  
**Governing Principle:** Physics-First, Outward · Least Invasive · Omni-field Awareness  
**Canon cross-references:** EPISTEMIC_FRAMEWORK.md, BIOPHOTON_09, C155, C156, C139, C160

---

## Why This Protocol Exists

Simulations in GAIA are not confirmation tools. They are interrogation tools. A simulation run to confirm what you already believe produces false confidence. A simulation run to discover what you do not yet know produces genuine knowledge.

For a system operating at the complexity and consequence level of GAIA — biological interfaces, quantum coherence measurement, distributed multi-agent governance, consent at population scale — a single simulation pass is insufficient epistemic basis for canon documentation or specification. Multiple passes are required because each pass reveals a layer of complexity that the previous pass was too coarse to reach.

This protocol defines the minimum simulation standard for all GAIA canon work.

---

## The Three-Pass Model

```
RESEARCH → SIM Pass 1: Discovery
                ↓
         What did it reveal?
         What was unexpected?
         What does the design actually do?
                ↓
RE-RESEARCH → SIM Pass 2: Refinement
                ↓
         Does the adjusted design hold under tighter conditions?
         What is the next layer of complexity?
                ↓
RE-RESEARCH → SIM Pass 3: Verification
                ↓
         VERIFY → DOCUMENT → SPECIFY
```

---

## Pass Definitions

### Pass 1 — Discovery
**Purpose:** Interrogate the design hypothesis. Find out what the design actually does, not what you predicted it would do.  
**Posture:** Expect the unexpected. A Pass 1 that returns only expected results is either too simple or too narrow.  
**Output:** A set of findings — confirmations, surprises, and failure modes — that inform Pass 2 research.  
**Canon status of results:** Research-grade. Not suitable for documentation or specification.  
**Framing:** Every Pass 1 simulation spec must include explicit **discovery questions** rather than expected confirmations.

### Pass 2 — Refinement
**Purpose:** Test the adjusted design under tighter, more specific conditions informed by Pass 1 findings.  
**Posture:** Tighter hypothesis. More specific parameters. Fewer unknowns than Pass 1.  
**Output:** Refined findings showing whether the adjusted design resolves Pass 1 failures and what new complexity emerges at the next layer.  
**Canon status of results:** Frontier-grade. May inform documentation drafts but not final canon.  
**Framing:** Every Pass 2 simulation spec must explicitly reference what Pass 1 revealed and how the design was adjusted in response.

### Pass 3 — Verification
**Purpose:** Verify a design that has survived two rounds of interrogation.  
**Posture:** The design is now mature. Pass 3 confirms it holds under the full range of specified conditions.  
**Output:** Verified results suitable for canon documentation and specification.  
**Canon status of results:** Verified. Suitable for documentation and specification.  
**Framing:** A Pass 3 failure is significant — it means something was missed at the research level, not the simulation level. It triggers a full research review, not just a parameter adjustment.

---

## Documentation and Specification Gates

| Action | Minimum Pass Required |
|---|---|
| File a research note | Pass 1 |
| Open a documentation issue | Pass 1 |
| Write a documentation draft | Pass 2 |
| Commit documentation to canon | Pass 3 |
| Write a specification | Pass 3 |
| Amend existing canon | Pass 3 |
| Close a Canon Tension issue | Pass 3 |
| Update CHANGELOG | Pass 3 |

---

## Simulation Naming Convention

All simulations follow this naming structure:

```
SIM-{number}_Pass{1|2|3}_{descriptive_name}.md
```

Examples:
- `SIM-016_Pass1_BCI_NextGen_Detector_Discovery.md`
- `SIM-016_Pass2_BCI_NextGen_Detector_Refinement.md`
- `SIM-016_Pass3_BCI_NextGen_Detector_Verification.md`
- `SIM-005_Pass2_Consent_Ledger_Sharded_Validation.md`

Where a simulation was run before this protocol was established (SIM-001 through SIM-016 Pass 1), it is retroactively classified as **Pass 1 — Discovery** unless it explicitly meets Pass 3 verification criteria.

---

## Retroactive Classification of Existing Simulations

All simulations run prior to this protocol are retroactively classified as follows:

| Simulation | Retroactive Classification | Rationale |
|---|---|---|
| SIM-001 | Pass 1 — Discovery | Initial coherence field baseline; single run |
| SIM-002 | Pass 1 — Discovery | BCI coherence budget; revealed CT-001 canon tension |
| SIM-003 | Pass 1 — Discovery | Memory consolidation decay; revealed CT-002 |
| SIM-004 | Pass 1 — Discovery | Multi-agent stress; revealed CT-003 |
| SIM-005 | Pass 1 — Discovery | Consent ledger throughput; revealed CT-004 |
| SIM-006 | Pass 1 — Discovery | KG drift; revealed CT-005 |
| SIM-007 | Pass 1 — Discovery | Pending classification |
| SIM-008 | Pass 1 — Discovery | BCI pipeline ceiling; confirmed CT-001 physics bound |
| SIM-016 | Pass 1 — Discovery | BCI next-gen detector; G-15 Tier 1 (pending) |
| SIM-017 | Pass 1 — Discovery | Persistent memory Option D; G-15 Tier 1 (pending) |

**Implication:** No existing simulation result is at Pass 3 verification status. Canon tensions CT-001 through CT-005 all have Pass 1 discovery results. Their resolution simulations (SIM-005 re-run, SIM-006 re-run, SIM-010) will be **Pass 2 — Refinement** runs. Pass 3 verification follows.

---

## Required Simulation Spec Structure

Every simulation specification must include the following sections:

```markdown
## Pass Classification
[Pass 1 — Discovery | Pass 2 — Refinement | Pass 3 — Verification]

## Pass Context
[For Pass 1: what is the design hypothesis being interrogated?]
[For Pass 2: what did Pass 1 reveal? How was the design adjusted?]
[For Pass 3: what did Pass 2 refine? What is being verified?]

## Discovery Questions (Pass 1) / Refinement Hypotheses (Pass 2) / Verification Criteria (Pass 3)
[Explicit questions or criteria — not expected confirmations]

## Parameters
[Full parameter specification]

## Success Conditions
[What constitutes a pass at this pass level]

## Failure Conditions
[What constitutes a fail and what it triggers]

## Output Artefacts
[What files this simulation produces]

## Canon Gate
[What canon action this simulation unlocks on pass]
```

---

## Epistemic Alignment

This protocol is the simulation-layer expression of EPISTEMIC_FRAMEWORK.md. The three passes map directly to the evidence levels:

| Pass | Evidence Level (EPISTEMIC_FRAMEWORK.md) |
|---|---|
| Pass 1 — Discovery | E3–E4: Limited or early research; theoretical/mechanistic |
| Pass 2 — Refinement | E2–E3: Limited primary research; emerging replication |
| Pass 3 — Verification | E1–E2: Replicated; approaching systematic review standard |

No simulation result is presented in canon documentation beyond its evidence level.

---

## The Rhythm Principle Applied

This protocol is a direct expression of G-15's governing Hermetic Principle — Rhythm. The three-pass cycle is not a bureaucratic requirement. It is the natural waveform of how genuine knowledge is produced:

- **Pass 1** is the inhale — compression, pressure-testing, discovery
- **Pass 2** is the adjustment — the pendulum finding its arc
- **Pass 3** is the exhale — releasing what is confirmed into the canon

Rushing from Pass 1 to documentation is forcing the swing. The pendulum does not force its arc — it follows the physics that has already prepared it.

---

## Amendment Log

| Date | Amendment | Authority |
|---|---|---|
| 2026-06-30 | Protocol established | R0GV3 (Seat I, The Coherence Council) |

---

*© 2026 Kyle Steen — All rights reserved.*
