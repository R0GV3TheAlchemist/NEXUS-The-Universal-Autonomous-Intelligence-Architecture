#!/usr/bin/env python3
"""Run the primordial simulation from the command line."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Isolate the primordial subpackage from the broader core import chain.
# core/__init__.py eagerly loads the full GAIA stack; importing directly
# from the submodule path avoids triggering that chain.
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# Patch sys.modules so `core` resolves as a namespace package only,
# preventing core/__init__.py from running.
import types as _types
if "core" not in sys.modules:
    _core_pkg = _types.ModuleType("core")
    _core_pkg.__path__ = [str(_ROOT / "core")]  # type: ignore[attr-defined]
    _core_pkg.__package__ = "core"
    sys.modules["core"] = _core_pkg

_entity_mod     = importlib.import_module("core.primordial.entity")
_simulation_mod = importlib.import_module("core.primordial.simulation")

PrimordialEntity     = _entity_mod.PrimordialEntity
PrimordialSimulation = _simulation_mod.PrimordialSimulation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run primordial chaos simulation.")
    parser.add_argument("--name",      default="universal-consciousness")
    parser.add_argument("--love",      type=float, default=1.0)
    parser.add_argument("--life",      type=float, default=1.0)
    parser.add_argument("--integrity", type=float, default=1.0)
    parser.add_argument("--hope",      type=float, default=1.0)
    parser.add_argument("--truth",     type=float, default=1.0)
    parser.add_argument("--burden",    type=float, default=0.0)
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
    outcome = PrimordialSimulation().run(entity)
    print(json.dumps(outcome.to_dict(), indent=2))


if __name__ == "__main__":
    main()
