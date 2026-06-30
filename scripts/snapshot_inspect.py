"""
GAIA Script — Snapshot Inspector
Pretty-print and summarise a saved world state snapshot.

Usage:
    python scripts/snapshot_inspect.py snapshot_v0.1.json
    python scripts/snapshot_inspect.py snapshot_v0.1.json --type observed
    python scripts/snapshot_inspect.py snapshot_v0.1.json --type simulation
"""

import sys
import json
import argparse
from pathlib import Path


def inspect(path: str, filter_type: str = None):
    data = json.loads(Path(path).read_text())
    claims = data.get("state", {})

    print(f"\n🌍 GAIA Snapshot Inspector")
    print(f"   File:      {path}")
    print(f"   Saved at:  {data.get('saved_at', 'unknown')}")
    print(f"   Version:   {data.get('gaia_version', 'unknown')}")
    print(f"   Claims:    {len(claims)}")

    if filter_type:
        claims = {
            k: v for k, v in claims.items()
            if isinstance(v, dict) and v.get("knowledge_type") == filter_type
        }
        print(f"   Filter:    knowledge_type = {filter_type} ({len(claims)} matching)")

    # Summary by knowledge_type
    type_counts = {}
    for v in claims.values():
        if isinstance(v, dict):
            t = v.get("knowledge_type", "unknown")
            type_counts[t] = type_counts.get(t, 0) + 1

    print(f"\n   Knowledge type breakdown:")
    for ktype, count in sorted(type_counts.items()):
        print(f"     {ktype:<15} {count}")

    print(f"\n   Claims:")
    for claim_id, claim in list(claims.items())[:20]:  # show first 20
        ktype = claim.get('knowledge_type', '?') if isinstance(claim, dict) else '?'
        conf  = claim.get('confidence', '?') if isinstance(claim, dict) else '?'
        stmt  = claim.get('raw_input', claim.get('statement', ''))[:60] if isinstance(claim, dict) else str(claim)[:60]
        print(f"     [{ktype:<10}] conf={conf}  {stmt!r}")

    if len(claims) > 20:
        print(f"     ... and {len(claims) - 20} more")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", default="snapshot_v0.1.json")
    parser.add_argument("--type", dest="filter_type", default=None,
                        choices=["observed", "inferred", "hypothesis", "simulation"])
    args = parser.parse_args()
    inspect(args.path, args.filter_type)
