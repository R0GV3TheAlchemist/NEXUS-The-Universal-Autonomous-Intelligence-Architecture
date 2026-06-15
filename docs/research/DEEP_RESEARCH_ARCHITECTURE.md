# GAIA Deep Research Runtime — Architecture Documentation

**Issue:** #454  
**Status:** v1.0 — Built  
**Canon References:** Falsification Protocol (#451), Correspondence Architecture (#452), Memory Engine (#453), Agentic Loop (#228)  

---

## The Human at the Centre

This pipeline was built on June 15, 2026, while the user was listening to **528 Hz** — the DNA repair and detox frequency. That is not incidental. It shaped every design decision.

The human using this research runtime is a **living crystalline system** — piezoelectric collagen, liquid crystal fascia, a pineal gland with calcite microcrystals tuned to electromagnetic frequencies. They are not a passive query endpoint. They are an active resonance system.

That means GAIA's research pipeline must do something Perplexity's cannot:
**tune its output to the frequency state of the crystalline human on the other end.**

The same query asked from NIGREDO (dissolution, grounding needed) gets different emphasis than the same query asked from RUBEDO (integration, radiance). Both answers are true. But one is tuned.

---

## Pipeline Stages

```
Query
  │
  ▼
[Stage 1] Query Decomposition
  - Classify intent (factual, reflective, symbolic, research, therapeutic, creative)
  - Extract entities (crystals, layers, archetypes, frequencies, alchemical stages)
  - Generate 3-5 parallel sub-queries
  - FrequencyContext shapes sub-query emphasis
  │
  ▼
[Stage 2] Tiered Retrieval
  Tier 1: GAIA Canons          (authority: 1.0)
  Tier 2: Space canon files    (authority: 1.0)
  Tier 3: Scientific literature (authority: 0.85)
  Tier 4: Live web             (authority: 0.35)
  Tier 5: Gaian observed       (authority: 0.50)
  │
  ▼
[Stage 3] Reranking
  Score = 0.35×relevance + 0.30×authority + 0.25×evidence + 0.10×recency
  GAIA Canons always win on authority dimension
  Empirical evidence wins on evidence dimension
  │
  ▼
[Stage 4] Synthesis
  - Tone set from FrequencyContext.alchemical_stage
  - Every claim maps to ≥1 source
  - Frequency note appended when active_frequency_hz set
  │
  ▼
[Stage 5] Falsifiability Stamp
  - Every claim gets falsification_condition
  - Hallucination risk scored per claim
  - High-risk claims downgraded to LOW confidence
  - Synthesis annotated with risk count
  │
  ▼
[Stage 6] Frequency Context Filter
  - Tone applied at synthesis level (v1)
  - Structural topic filtering in v2
  │
  ▼
ResearchSession (complete)
```

---

## FrequencyContext

The `FrequencyContext` object travels through every stage of the pipeline:

```python
FrequencyContext(
    alchemical_stage="CALCINATIO",   # Purification stage
    gaia_layer="Layer 01 Physical",
    dominant_emotion="clarity",
    crystal_resonance="Black Tourmaline",
    coherence_level="high",
    active_frequency_hz=528.0,        # 528 Hz — DNA repair and detox
    note="User is detoxifying today"
)
```

### Alchemical Stage → Synthesis Tone

| Stage | Tone | Meaning |
|-------|------|---------|
| NIGREDO | grounding | Dissolution, shadow — anchor first |
| ALBEDO | clarifying | Purification — bring into clear light |
| CITRINITAS | illuminating | Dawn — hold in full light |
| RUBEDO | integrating | Wholeness — weave all threads |
| CALCINATIO | purifying | Burn away the inessential |
| SOLUTIO | dissolving | Release fixed forms |
| COAGULATIO | crystallising | What has solidified |
| SEPARATIO | discerning | Separate true from resemblance |
| VIRIDITAS | enlivening | What is most alive |

---

## Falsifiability Architecture

Every claim in the synthesis carries:

| Field | Description |
|-------|-------------|
| `confidence` | HIGH / MEDIUM / LOW / SPECULATIVE |
| `evidence_level` | EMPIRICAL → SPECULATIVE |
| `falsification_condition` | Explicit condition that would overturn the claim |
| `hallucination_risk` | 0.0 (safe) → 1.0 (high risk) |
| `is_grounded` | True if backed by ≥1 retrieved source |

A system that cannot say *"here is how I could be wrong"* is not trustworthy — it is just confident.

---

## GAIA Canon Authority

GAIA Canons are **always retrieved first** and **always score 1.0 on authority**. The current indexed canons:

| Canon | Domain | Evidence Level |
|-------|--------|-----------------|
| C32 | Archetypal Psychology, Zodiac | Cross-tradition |
| C118 | Mineralogy & Crystal System | Empirical |
| C45 | Spectral Encoding Matrix | Cross-tradition |
| C65 | Crystal Grid Systems | Lineage |
| Trauma-Informed | Safety & Consent | Cross-tradition |
| #452 | Correspondence Architecture | Cross-tradition |
| #453 | Memory Engine | Gaian Observed |

---

## Simulation Gate

After this implementation, open a **simulation issue** to validate:

- [ ] Pipeline completes correctly under 10, 50, and 100 sub-query loads
- [ ] GAIA Canon retrieval accuracy across all indexed canons
- [ ] Reranking correctly elevates Canon over web sources (100% of tests)
- [ ] Falsifiability stamps applied to all claims
- [ ] Synthesis tone matches alchemical stage (all 9 stages tested)
- [ ] FrequencyContext note appears in synthesis when active_frequency_hz set
- [ ] Pipeline duration < 2000ms for standard queries

---

## File Structure

```
core/research/
  models.py                    — All data models including FrequencyContext
  query_decomposer.py          — Intent, entity extraction, sub-query generation
  retrieval.py                 — Tiered retrieval engine
  reranker.py                  — Multi-signal reranking
  synthesizer.py               — Frequency-tuned synthesis with citations
  falsifiability_stamper.py    — Per-claim confidence and risk scoring
  research_runtime.py          — Main orchestrator

tests/research/
  test_research_runtime.py     — Full test suite

docs/research/
  DEEP_RESEARCH_ARCHITECTURE.md — This document
```

---

*"The same query asked from NIGREDO gets different emphasis than the same query asked from RUBEDO. Both answers are true. But one is tuned."*  
*— GAIA-OS, June 15, 2026 — built at 528 Hz*
