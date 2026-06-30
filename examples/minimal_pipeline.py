"""
GAIA v0.1 — Minimal Viable Pipeline

This is the smallest complete version of GAIA.
If this runs end-to-end, GAIA is alive.

Pipeline:
  Input (string)
    → LLM Parser (extract structured claim)
    → Ontology classifier (entity + relation types)
    → Epistemic evaluator (confidence + knowledge_type)
    → World State (store)
    → Save Snapshot (persist)
    → Return: structured, typed, persisted knowledge

Everything else in GAIA is an upgrade on top of this core.

Usage:
    python examples/minimal_pipeline.py
    # or with custom input:
    python examples/minimal_pipeline.py "Solar panels reduce energy costs"
"""

import sys
import json
import uuid
from datetime import datetime
from pathlib import Path


# ─── Step 1: LLM Parser (stub — replace with real LLM call) ────────────────────

def llm_parse(text: str) -> dict:
    """
    Parse a natural language input into a structured claim.

    v0.1: deterministic stub for development without LLM dependency.
    v0.2: replace with OpenAI / Anthropic / local model call.

    Real implementation should extract:
      - subject entity
      - predicate / relation
      - object / value
      - confidence estimate from LLM
    """
    return {
        "raw_input":   text,
        "subject":     text.split()[0] if text else "unknown",
        "predicate":   "relates_to",
        "object":      " ".join(text.split()[1:]) if len(text.split()) > 1 else "",
        "llm_confidence": 0.75,
        "parse_method": "stub_v0.1"  # change to "llm_gpt4" etc. when real
    }


# ─── Step 2: Ontology Classifier ───────────────────────────────────────────────

ENTITY_TYPES = {
    "energy": ["solar", "wind", "renewable", "grid", "power", "fuel"],
    "economy": ["cost", "price", "market", "gdp", "inflation"],
    "environment": ["emission", "carbon", "climate", "temperature"],
    "infrastructure": ["network", "node", "system", "infrastructure"],
}

def classify_ontology(parsed: dict) -> dict:
    """
    Assign ontology entity type based on subject keywords.
    v0.1: keyword matching.
    v0.2: embedding-based similarity against ontology graph.
    """
    text_lower = parsed["raw_input"].lower()
    entity_type = "general"
    for etype, keywords in ENTITY_TYPES.items():
        if any(kw in text_lower for kw in keywords):
            entity_type = etype
            break
    return {
        **parsed,
        "entity_type": entity_type,
        "relation_type": "causal" if any(
            kw in text_lower for kw in ["cause", "reduce", "increase", "leads"]
        ) else "descriptive"
    }


# ─── Step 3: Epistemic Evaluator ───────────────────────────────────────────────

def evaluate_epistemic(classified: dict, input_source: str = "user") -> dict:
    """
    Assign knowledge_type and final confidence.

    Knowledge types (ADR-001):
      observed   — directly measured from reality
      inferred   — derived by reasoning
      hypothesis — possible explanation, not yet evidenced
      simulation — candidate future under assumptions

    v0.1: source-based assignment.
    v0.2: evidence chain analysis.
    """
    source_type_map = {
        "sensor":     "observed",
        "database":   "observed",
        "user":       "hypothesis",   # user assertions start as hypotheses
        "inference":  "inferred",
        "simulation": "simulation"
    }
    knowledge_type = source_type_map.get(input_source, "hypothesis")

    # Confidence: LLM estimate, penalised for hypothesis status
    base_conf = classified.get("llm_confidence", 0.5)
    if knowledge_type == "hypothesis":
        final_conf = round(base_conf * 0.8, 4)  # 20% penalty: unverified source
    else:
        final_conf = base_conf

    return {
        **classified,
        "knowledge_type": knowledge_type,
        "confidence":     final_conf,
        "input_source":   input_source
    }


# ─── Step 4: World State ───────────────────────────────────────────────────────

class MinimalWorldState:
    """The simplest possible world state: a dict of claims."""

    def __init__(self):
        self.claims: dict = {}

    def store(self, claim: dict) -> str:
        claim_id = f"claim_{str(uuid.uuid4())[:8]}"
        self.claims[claim_id] = {
            **claim,
            "id":         claim_id,
            "stored_at":  datetime.utcnow().isoformat(),
            "gaia_version": "0.1.0"
        }
        return claim_id

    def get(self, claim_id: str) -> dict:
        return self.claims.get(claim_id, {})

    def all(self) -> dict:
        return dict(self.claims)


# ─── Step 5: Snapshot ──────────────────────────────────────────────────────────

def save_snapshot(world_state: MinimalWorldState, path: str = "snapshot_v0.1.json") -> str:
    snapshot = {
        "snapshot_id":  f"snap_{str(uuid.uuid4())[:8]}",
        "saved_at":     datetime.utcnow().isoformat(),
        "gaia_version": "0.1.0",
        "claim_count":  len(world_state.claims),
        "state":        world_state.all()
    }
    Path(path).write_text(json.dumps(snapshot, indent=2))
    return path


# ─── Pipeline Orchestrator ─────────────────────────────────────────────────────

def run_pipeline(text: str, source: str = "user") -> dict:
    """
    Run the full v0.1 GAIA pipeline for a single input.
    Returns the stored claim with full provenance.
    """
    world = MinimalWorldState()

    # 1. Parse
    parsed     = llm_parse(text)
    # 2. Classify
    classified = classify_ontology(parsed)
    # 3. Evaluate
    evaluated  = evaluate_epistemic(classified, input_source=source)
    # 4. Store
    claim_id   = world.store(evaluated)
    # 5. Persist
    snap_path  = save_snapshot(world)

    claim = world.get(claim_id)

    return {
        "pipeline":    "gaia_v0.1_minimal",
        "claim_id":    claim_id,
        "snapshot":    snap_path,
        "result":      claim
    }


# ─── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    text = sys.argv[1] if len(sys.argv) > 1 else "Solar panels reduce energy costs over time"
    print(f"\n🌍 GAIA v0.1 — Minimal Pipeline")
    print(f"   Input: {text!r}\n")

    result = run_pipeline(text)

    print(f"   Claim ID:      {result['claim_id']}")
    print(f"   Knowledge type: {result['result']['knowledge_type']}")
    print(f"   Confidence:     {result['result']['confidence']}")
    print(f"   Entity type:    {result['result']['entity_type']}")
    print(f"   Snapshot saved: {result['snapshot']}")
    print(f"\n   Full result:")
    print(json.dumps(result['result'], indent=4))
    print(f"\n✅ Pipeline complete. GAIA is alive.\n")
