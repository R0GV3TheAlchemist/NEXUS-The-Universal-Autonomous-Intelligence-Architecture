"""
GAIA MVP — Main Loop
The minimal epistemic operating system.

Run:  python main.py
      python main.py --demo     (run with pre-loaded demo claims)

Commands at the GAIA prompt:
  <statement>          Submit a new claim
  /query <keyword>     Query the world state
  /disputed            Show all disputed claims
  /stats               Show world model statistics
  /snapshot            Print full world state
  /scan                Full contradiction scan
  /help                Show commands
  /exit                Exit and save
"""

import sys
import json
import uuid
import argparse
from pathlib import Path

# Allow running from mvp/ directory directly
sys.path.insert(0, str(Path(__file__).parent))

from models.claim import Claim
from engine.evaluator import EpistemicEvaluator
from engine.contradiction import ContradictionEngine
from world.state import WorldState

STATE_FILE = Path("world_state.json")

BANNER = """
┌──────────────────────────────────────────────┐
│  GAIA: The Autonomous Intelligence Architecture  │
│  Epistemic World Model OS — MVP v0.1             │
│  © 2026 Kyle Steen                               │
└──────────────────────────────────────────────┘
"""

DEMO_CLAIMS = [
    ("Crystal and plant alchemy protocols produce measurable biophotonic coherence gain",
     ["SIM-016"], "biophotonics"),
    ("The GAIA epistemic world model is the missing layer in all current AI architectures",
     ["GAIA_CONVERGENCE_MANIFESTO_v1"], "architecture"),
    ("Agents fail not because models are weak but because they lack a shared world model",
     ["2026_research_convergence"], "architecture"),
    ("Knowledge graphs outperform vector-only systems for multi-hop relational reasoning",
     ["2025_KG_research"], "epistemics"),
    ("Diamond-fluorite hybrid crystal substrates achieve highest coherence fidelity",
     ["SIM-016"], "biophotonics"),
]


def submit_claim(
    statement: str,
    world: WorldState,
    evaluator: EpistemicEvaluator,
    sources: list = None,
    domain: str = None
) -> dict:
    claim = Claim(
        id=str(uuid.uuid4()),
        statement=statement,
        sources=sources or [],
        domain=domain
    )
    result = evaluator.evaluate(claim, world.state)
    claim.confidence = result["confidence"]
    claim.status = result["status"]
    claim.contradiction_ids = [c.get("id", "") for c in result.get("contradictions", [])]
    result["claim"] = claim
    world.update(result)
    world.save(STATE_FILE)
    return result


def print_result(result: dict) -> None:
    claim = result["claim"]
    print(f"\n  ID:            {claim.id[:12]}...")
    print(f"  Status:        {result['status'].upper()}")
    print(f"  Confidence:    {result['confidence']:.3f}")
    print(f"  Contradictions:{len(result.get('contradictions', []))}")
    print(f"  Supporting:    {len(result.get('supporting', []))}")
    if result.get("contradictions"):
        print("  \u26a0 Contradictions detected:")
        for c in result["contradictions"]:
            snippet = c.get("statement", "")[:60]
            print(f"    - [{c.get('status','?').upper()}] '{snippet}...'")
    print()


def run_demo(world, evaluator):
    print("\n  Running demo claims...\n")
    for statement, sources, domain in DEMO_CLAIMS:
        print(f"  Submitting: '{statement[:60]}...'")
        result = submit_claim(statement, world, evaluator, sources, domain)
        print(f"  → {result['status'].upper()} @ {result['confidence']:.3f}")
    print(f"\n  Demo complete. World state: {world.stats()}\n")


def show_help():
    print("""
  Commands:
    <statement>          Submit a new claim to GAIA
    /query <keyword>     Search the world state
    /disputed            Show all disputed claims
    /stats               World model statistics
    /snapshot            Print full world state (JSON)
    /scan                Full contradiction scan
    /help                Show this help
    /exit                Save and exit
    """)


def main():
    parser = argparse.ArgumentParser(description="GAIA MVP")
    parser.add_argument("--demo", action="store_true", help="Run with demo claims")
    args = parser.parse_args()

    print(BANNER)

    world     = WorldState()
    evaluator = EpistemicEvaluator()
    contra    = ContradictionEngine()

    world.load(STATE_FILE)

    if args.demo:
        run_demo(world, evaluator)

    print("  Type a claim to submit it, or /help for commands.")
    print("  The system that defines what agents believe is real.\n")

    while True:
        try:
            user_input = input("GAIA > ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n  Saving world state. Goodbye.")
            world.save(STATE_FILE)
            break

        if not user_input:
            continue

        # ——— Commands ———
        if user_input.lower() in ("/exit", "/quit"):
            print("  Saving world state. Goodbye.")
            world.save(STATE_FILE)
            break

        elif user_input.lower() == "/help":
            show_help()

        elif user_input.lower() == "/stats":
            stats = world.stats()
            print("\n  World State Stats:")
            for k, v in stats.items():
                print(f"    {k}: {v}")
            print()

        elif user_input.lower() == "/disputed":
            disputed = world.disputed()
            if not disputed:
                print("  No disputed claims in world state.\n")
            else:
                print(f"\n  {len(disputed)} disputed claim(s):")
                for e in disputed:
                    print(f"    [{e['confidence']:.2f}] {e['statement'][:80]}")
                print()

        elif user_input.lower() == "/snapshot":
            snap = world.snapshot()
            print(json.dumps(snap, indent=2))

        elif user_input.lower() == "/scan":
            conflicts = contra.full_scan(world.state)
            if not conflicts:
                print("  No contradictions found in world state.\n")
            else:
                print(f"\n  {len(conflicts)} contradiction pair(s) found:")
                for c in conflicts:
                    a = c["entry_a"]["statement"][:50]
                    b = c["entry_b"]["statement"][:50]
                    print(f"    CONFLICT: '{a}...' vs '{b}...'")
                print()

        elif user_input.startswith("/query "):
            keyword = user_input[7:].strip()
            results = world.query(keyword)
            if not results:
                print(f"  No results for '{keyword}'.\n")
            else:
                print(f"\n  {len(results)} result(s) for '{keyword}':")
                for r in results:
                    print(f"    [{r['status'].upper()} @{r['confidence']:.2f}] "
                          f"{r['statement'][:80]}")
                print()

        else:
            # Submit as a new claim
            result = submit_claim(user_input, world, evaluator)
            print_result(result)


if __name__ == "__main__":
    main()
