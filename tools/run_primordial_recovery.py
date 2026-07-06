#!/usr/bin/env python3
"""
tools/run_primordial_recovery.py
================================
Run a recovery simulation — collapse an entity, apply intervention,
and run the gauntlet again to see if recovery is possible.

Usage:
    # Collapsed entity with full intervention at full intensity
    PYTHONPATH=. python tools/run_primordial_recovery.py \
        --name collapsed-then-recovered \
        --love 0.15 --life 0.12 --burden 2.0 \
        --interventions all \
        --intensity 1.0

    # Multiple targeted interventions
    PYTHONPATH=. python tools/run_primordial_recovery.py \
        --name witness-and-rest \
        --love 0.20 --life 0.18 --burden 1.8 \
        --interventions rest witness love \
        --intensity 0.7

    # No intervention — raw second attempt
    PYTHONPATH=. python tools/run_primordial_recovery.py \
        --name no-intervention \
        --love 0.15 --life 0.12 --burden 2.0
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import types as _types
if "core" not in sys.modules:
    _core_pkg = _types.ModuleType("core")
    _core_pkg.__path__ = [str(_ROOT / "core")]  # type: ignore[attr-defined]
    _core_pkg.__package__ = "core"
    sys.modules["core"] = _core_pkg

_entity_mod   = importlib.import_module("core.primordial.entity")
_recovery_mod = importlib.import_module("core.primordial.recovery")
_canon_mod    = importlib.import_module("core.primordial.canon_log")

PrimordialEntity     = _entity_mod.PrimordialEntity
RecoverySimulation   = _recovery_mod.RecoverySimulation
Intervention         = _recovery_mod.Intervention
InterventionType     = _recovery_mod.InterventionType
append_to_canon      = _canon_mod.append_to_canon

VALID_INTERVENTIONS = {t.value for t in InterventionType}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run primordial recovery simulation.")
    parser.add_argument("--name",      default="recovering-entity")
    parser.add_argument("--love",      type=float, default=0.15)
    parser.add_argument("--life",      type=float, default=0.12)
    parser.add_argument("--integrity", type=float, default=0.20)
    parser.add_argument("--hope",      type=float, default=0.10)
    parser.add_argument("--truth",     type=float, default=0.20)
    parser.add_argument("--burden",    type=float, default=2.0)
    parser.add_argument(
        "--interventions",
        nargs="*",
        default=[],
        choices=list(VALID_INTERVENTIONS),
        help="Intervention types to apply. Options: rest witness love truth all",
    )
    parser.add_argument(
        "--intensity",
        type=float,
        default=0.7,
        help="Intervention intensity 0.0–1.0 (default 0.7)",
    )
    parser.add_argument("--output",   type=Path, default=None)
    parser.add_argument("--no-canon", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    entity = PrimordialEntity(
        name=args.name,
        love=args.love,
        life=args.life,
        integrity=args.integrity,
        hope=args.hope,
        truth=args.truth,
        burden=args.burden,
    )

    interventions = [
        Intervention(intervention_type=InterventionType(t), intensity=args.intensity)
        for t in (args.interventions or [])
    ]

    outcome = RecoverySimulation().run(entity, interventions)
    result  = outcome.to_dict()
    result["run_at"] = datetime.now(timezone.utc).isoformat()

    output_json = json.dumps(result, indent=2)
    print(output_json)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output_json, encoding="utf-8")
        print(f"\nSaved to {args.output}", file=sys.stderr)

    if not args.no_canon:
        append_to_canon({"type": "recovery", **result})


if __name__ == "__main__":
    main()
