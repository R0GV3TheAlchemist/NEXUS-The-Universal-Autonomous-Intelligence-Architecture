"""
GAIA v0.2 — Main Entry Point
Ontology-aware epistemic world model OS.

Run:
  python main.py          # interactive prompt
  python main.py --demo   # pre-loaded demo with entities + claims

Commands:
  <statement>              Submit a claim
  /entity <type> <name>    Register a new entity
  /link <a> <b> <type>     Link two entity names with a relationship
  /query <keyword>         Query world state
  /ontology                Show ontology stats
  /stats                   Show world model stats
  /snapshot                Print full world state JSON
  /disputed                Show disputed claims
  /scan                    Full contradiction scan
  /help                    Show commands
  /exit                    Save and exit
"""

import json
import logging
import argparse
from pathlib import Path

from gaia.ontology.entity import Entity
from gaia.ontology.relationship import Relationship
from gaia.ontology.claim import Claim
from gaia.ontology.registry import OntologyRegistry
from gaia.epistemics.evaluator import EpistemicEvaluator
from gaia.world.state import WorldState
from gaia.world.graph import WorldGraph
from gaia.world.persistence import WorldPersistence
from gaia.governance.policy_engine import PolicyEngine

# ---------------------------------------------------------------------------
# Runtime layer — PrimordialSession + PersistenceManager via server/startup.py
# Imported here so gaps 1-3 (gaian_named, fragment_written, epoch_closed) are
# closed at boot.  Graceful fallback keeps the v0.2 ontology CLI working even
# in environments where the runtime layer is not yet installed.
# ---------------------------------------------------------------------------
try:
    import os
    from server.startup import bootstrap_gaia
    _RUNTIME_AVAILABLE = True
except ImportError:
    _RUNTIME_AVAILABLE = False

logger = logging.getLogger("gaia.main")

STATE_FILE = Path("world_state.json")
PERSISTENCE_ROOT = os.environ.get("GAIA_PERSISTENCE_ROOT", "gaia_memory") \
    if _RUNTIME_AVAILABLE else "gaia_memory"

BANNER = """
┌──────────────────────────────────────────────┐
│  GAIA: The Autonomous Intelligence Architecture  │
│  Epistemic World Model OS — v0.2                 │
│  Ontology-aware. Truth-structured. Reality graph  │
│  © 2026 Kyle Steen                               │
└──────────────────────────────────────────────┘
"""

DEMO_ENTITIES = [
    ("CONCEPT",     "Biophotonic Coherence",    "biophotonics"),
    ("PROCESS",     "Crystal Alchemy",          "biophotonics"),
    ("PROCESS",     "Plant Alchemy",            "biophotonics"),
    ("SYSTEM",      "GAIA Epistemic OS",         "architecture"),
    ("CONCEPT",     "Epistemic World Model",    "architecture"),
    ("CONCEPT",     "Ontology Layer",           "architecture"),
    ("DOMAIN",      "AI Architecture",          "architecture"),
    ("MEASUREMENT", "Coherence Gain 0.47",      "biophotonics"),
]

DEMO_CLAIMS = [
    ("Crystal and plant alchemy protocols produce synergistic biophotonic coherence gain",
     ["SIM-016"], "biophotonics"),
    ("GAIA epistemic world model is the missing layer in all current AI architectures",
     ["GAIA_CONVERGENCE_MANIFESTO_v1"], "architecture"),
    ("Agents fail because they lack a shared coherent world model not because models are weak",
     ["2026_research_convergence"], "architecture"),
    ("Knowledge graphs outperform vector-only systems for multi-hop relational reasoning",
     ["2025_KG_research"], "epistemics"),
    ("Ontology is unavoidable in production AI systems that reason across domains",
     ["2026_agent_research"], "architecture"),
]


def build_systems():
    ontology   = OntologyRegistry()
    evaluator  = EpistemicEvaluator()
    world      = WorldState()
    graph      = WorldGraph()
    persister  = WorldPersistence()
    policy     = PolicyEngine()
    kb: dict   = {}  # claim_id → Claim (in-memory knowledge base)
    return ontology, evaluator, world, graph, persister, policy, kb


def submit_claim(statement, sources, domain, entities_ids,
                 ontology, evaluator, world, policy, kb):
    claim = Claim(
        statement=statement,
        sources=sources or [],
        domain=domain,
        entities=entities_ids or []
    )
    check = policy.check_claim(claim)
    if not check["permitted"]:
        print(f"  ⛔ Policy violation: {check['notes']}")
        return None

    result = evaluator.evaluate(claim, ontology, kb)
    claim.confidence = result["confidence"]
    claim.status = result["status"]

    kb[claim.id] = claim
    ontology.add_claim(claim)
    world.update(result)
    return result


def run_demo(ontology, evaluator, world, graph, policy, kb):
    print("\n  Loading demo entities...")
    entity_map = {}  # name → entity
    for etype, ename, domain in DEMO_ENTITIES:
        e = Entity(type=etype, name=ename, domain=domain)
        ontology.add_entity(e)
        graph.add_entity_node(e)
        entity_map[ename] = e
        print(f"  + Entity: [{etype}] {ename}")

    # Wire some relationships
    pairs = [
        ("Crystal Alchemy", "Biophotonic Coherence", "ENABLES", 0.82),
        ("Plant Alchemy",   "Biophotonic Coherence", "ENABLES", 0.79),
        ("GAIA Epistemic OS", "Epistemic World Model", "IMPLEMENTS", 0.95),
        ("Ontology Layer",  "GAIA Epistemic OS",    "PART_OF",  0.99),
    ]
    print("\n  Wiring relationships...")
    for a, b, rtype, conf in pairs:
        if a in entity_map and b in entity_map:
            rel = Relationship(
                from_entity=entity_map[a].id,
                to_entity=entity_map[b].id,
                type=rtype,
                confidence=conf,
                source="demo"
            )
            ontology.add_relationship(rel)
            graph.add_relationship_edge(rel)
            print(f"  + Relationship: {a} --[{rtype}]--> {b}")

    print("\n  Submitting demo claims...")
    for statement, sources, domain in DEMO_CLAIMS:
        entity_ids = [
            e.id for e in ontology.all_entities()
            if any(word.lower() in statement.lower()
                   for word in e.name.split())
        ]
        result = submit_claim(
            statement, sources, domain, entity_ids,
            ontology, evaluator, world, policy, kb
        )
        if result:
            print(f"  → [{result['status'].upper()} @{result['confidence']:.3f}] "
                  f"{statement[:60]}...")

    print("\n  Demo complete.")
    print(f"  Ontology: {ontology}")
    print(f"  Graph:    {graph}")
    print(f"  World:    {world}\n")


def show_help():
    print("""
  Commands:
    <statement>              Submit a claim (free text)
    /entity <TYPE> <name>    Register entity (e.g. /entity CONCEPT Consciousness)
    /link <a> <b> <TYPE>     Link entities by name (e.g. /link Alchemy Coherence ENABLES)
    /query <keyword>         Search world state
    /ontology                Ontology registry stats
    /graph                   World graph stats
    /stats                   World model stats
    /snapshot                Full world state JSON
    /disputed                Show disputed claims
    /help                    This help
    /exit                    Save and exit
    """)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()

    print(BANNER)
    ontology, evaluator, world, graph, persister, policy, kb = build_systems()

    # ------------------------------------------------------------------
    # Runtime layer bootstrap — wires persistence hooks for gaps 1-3.
    # session.end() must be called on every exit path so the
    # session_ended hook flushes in-flight writes.
    # ------------------------------------------------------------------
    _session = None
    if _RUNTIME_AVAILABLE:
        try:
            _session, _manager = bootstrap_gaia(persistence_root=PERSISTENCE_ROOT)
            logger.info("[main] GAIA runtime layer active — persistence_root=%s",
                        PERSISTENCE_ROOT)
        except Exception as exc:
            logger.warning("[main] bootstrap_gaia() failed (%s); "
                           "running without persistence hooks.", exc)
    else:
        logger.warning("[main] server.startup not importable; "
                       "running without persistence hooks (ontology CLI mode).")

    # Load prior world-model state
    prior = persister.load(STATE_FILE)
    if prior.get("state"):
        world._state = prior["state"]
        world._update_count = prior.get("update_count", 0)
        print(f"  Resumed: {len(world._state)} prior entries.\n")

    if args.demo:
        run_demo(ontology, evaluator, world, graph, policy, kb)

    print("  Type a claim, or /help for commands.\n")

    while True:
        try:
            user_input = input("GAIA > ").strip()
        except (KeyboardInterrupt, EOFError):
            persister.save(world.snapshot(), STATE_FILE)
            if _session is not None:
                _session.end()
            print("\n  World state saved. Goodbye.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("/exit", "/quit"):
            persister.save(world.snapshot(), STATE_FILE)
            if _session is not None:
                _session.end()
            print("  World state saved. Goodbye.")
            break

        elif user_input.lower() == "/help":
            show_help()

        elif user_input.lower() == "/ontology":
            print(f"\n  {ontology}")
            for k, v in ontology.stats().items():
                print(f"    {k}: {v}")
            print()

        elif user_input.lower() == "/graph":
            print(f"\n  {graph}\n")

        elif user_input.lower() == "/stats":
            for k, v in world.stats().items():
                print(f"    {k}: {v}")
            print()

        elif user_input.lower() == "/snapshot":
            print(json.dumps(world.snapshot(), indent=2, default=str))

        elif user_input.lower() == "/disputed":
            disputed = world.disputed()
            print(f"\n  {len(disputed)} disputed:")
            for e in disputed:
                print(f"    [{e['confidence']:.2f}] {e['statement'][:80]}")
            print()

        elif user_input.startswith("/entity "):
            parts = user_input[8:].strip().split(" ", 1)
            if len(parts) < 2:
                print("  Usage: /entity <TYPE> <name>")
            else:
                etype, ename = parts[0].upper(), parts[1]
                try:
                    e = Entity(type=etype, name=ename)
                    ontology.add_entity(e)
                    graph.add_entity_node(e)
                    print(f"  + Entity registered: [{etype}] '{ename}' (id={e.id[:8]}...)")
                except ValueError as err:
                    print(f"  Error: {err}")

        elif user_input.startswith("/link "):
            parts = user_input[6:].strip().split()
            if len(parts) < 3:
                print("  Usage: /link <entity_a_name_word> <entity_b_name_word> <TYPE>")
            else:
                name_a, name_b, rtype = parts[0], parts[1], parts[2].upper()
                ea = ontology.find_entity_by_name(name_a)
                eb = ontology.find_entity_by_name(name_b)
                if not ea or not eb:
                    print(f"  Could not find entities: '{name_a}' or '{name_b}'")
                else:
                    try:
                        rel = Relationship(
                            from_entity=ea.id, to_entity=eb.id, type=rtype
                        )
                        ontology.add_relationship(rel)
                        graph.add_relationship_edge(rel)
                        print(f"  + Linked: '{ea.name}' --[{rtype}]--> '{eb.name}'")
                    except ValueError as err:
                        print(f"  Error: {err}")

        elif user_input.startswith("/query "):
            keyword = user_input[7:].strip()
            results = world.query(keyword)
            print(f"\n  {len(results)} result(s) for '{keyword}':")
            for r in results:
                print(f"    [{r['status'].upper()} @{r['confidence']:.2f}] "
                      f"{r['statement'][:80]}")
            print()

        else:
            # Auto-match entities in the statement
            entity_ids = [
                e.id for e in ontology.all_entities()
                if any(word.lower() in user_input.lower()
                       for word in e.name.split())
            ]
            result = submit_claim(
                user_input, [], None, entity_ids,
                ontology, evaluator, world, policy, kb
            )
            if result:
                claim = result["claim"]
                print(f"\n  Status:        {result['status'].upper()}")
                print(f"  Confidence:    {result['confidence']:.3f}")
                print(f"  Entities:      {len(claim.entities)} matched")
                print(f"  Contradictions:{len(result.get('contradictions', []))}")
                print(f"  Method:        {result.get('evaluation_method', 'v0.2')}\n")


if __name__ == "__main__":
    main()
