#!/usr/bin/env python3
"""GAIA-OS bulk crystal correspondence importer.

Usage
-----
    # Import all JSON files in a directory
    python scripts/import_crystals.py data/correspondence/

    # Dry run — validate only, no DB writes
    python scripts/import_crystals.py data/correspondence/ --dry-run

    # Continue after per-file errors (partial import)
    python scripts/import_crystals.py data/correspondence/ --continue-on-error

    # Recursive directory search
    python scripts/import_crystals.py data/ --recursive

    # Verbose: print extracted scalar preview per crystal
    python scripts/import_crystals.py data/correspondence/ --verbose

    # Combine flags
    python scripts/import_crystals.py data/correspondence/ --dry-run --verbose

Environment
-----------
    DATABASE_URL  PostgreSQL connection string.
                  Falls back to .env file if present.

Exit codes
----------
    0  All files imported successfully (or dry-run passed).
    1  One or more files failed validation or import.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Optional: load .env if python-dotenv is installed
# ---------------------------------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import sqlalchemy as sa
from sqlalchemy.orm import Session

# Local imports (assumes repo root is on PYTHONPATH)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.crystal_correspondence.ingestion import (
    clear_validation_errors,
    get_validation_errors,
    ingest_json_file,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("import_crystals")

COL_W = {"file": 32, "id": 36, "status": 10, "stage": 16, "coh": 8, "chakra": 20, "review": 10}


def _hr(char: str = "─") -> str:
    total = sum(COL_W.values()) + len(COL_W) * 3 + 1
    return char * total


def _row(*cells) -> str:
    widths = list(COL_W.values())
    parts = [f" {str(c)[:w]:<{w}} " for c, w in zip(cells, widths)]
    return "│" + "│".join(parts) + "│"


def _header() -> list[str]:
    return [
        _hr("┌" if False else "─"),
        _row("File", "subject_id", "Status", "Alch. Stage", "Coh.", "Primary Chakra", "Review"),
        _hr("├" if False else "─"),
    ]


def _discover_files(directory: Path, recursive: bool) -> list[Path]:
    pattern = "**/*.json" if recursive else "*.json"
    files = sorted(directory.glob(pattern))
    if not files:
        logger.warning("No .json files found in %s", directory)
    return files


def _preview_scalars(payload: dict[str, Any]) -> None:
    corr = payload.get("correspondences", {})
    pp   = corr.get("physical_properties", {})
    alch = corr.get("alchemical", {})
    cp   = corr.get("consequential_properties", {})
    chakras = corr.get("chakra_system", [])

    print(f"    ├ crystal_system      : {pp.get('crystal_system', '—')}")
    print(f"    ├ mohs_hardness       : {pp.get('mohs_hardness', '—')}")
    print(f"    ├ piezoelectric       : {pp.get('piezoelectric', '—')}")
    print(f"    ├ alchemical_stage    : {alch.get('stage_primary', '—')}")
    print(f"    ├ transmutation       : {alch.get('transmutation_corridor', '—')}")
    print(f"    ├ coherence_scalar    : {cp.get('coherence_impact', {}).get('scalar', '—')}")
    print(f"    ├ grey_state_risk     : {cp.get('grey_state_risk', {}).get('mitigates', [])!r}")
    healing = corr.get("healing", {})
    phys    = [h.get("description", "")[:60] for h in healing.get("physical", [])[:2]]
    print(f"    ├ healing.physical    : {phys or '—'}")
    freqs   = [f.get("hz") for f in corr.get("resonant_frequencies", [])[:3]]
    print(f"    ├ resonant_hz         : {freqs or '—'}")
    print(f"    └ primary_chakra      : {chakras[0].get('chakra') if chakras else '—'}")


def _run_import(
    files: list[Path],
    session: Session,
    dry_run: bool,
    verbose: bool,
    continue_on_error: bool,
) -> tuple[list[dict], list[dict]]:
    """
    Returns (successes, failures).
    Each success: {file, subject_id, alch_stage, coherence, chakra, review}
    Each failure: {file, error}
    """
    successes: list[dict] = []
    failures: list[dict] = []

    for path in files:
        try:
            with path.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)

            if verbose:
                print(f"\n  ▶ {path.name}  [{payload.get('subject_id', '?')}]")
                _preview_scalars(payload)

            row = ingest_json_file(
                session,
                path,
                changed_by="import_crystals.py",
                change_note=f"bulk import {'(dry-run) ' if dry_run else ''}via import_crystals.py",
                dry_run=dry_run,
            )

            successes.append({
                "file": path.name,
                "subject_id": row.subject_id,
                "alch_stage": row.alchemical_stage_primary or row.alchemical_stage or "—",
                "coherence": str(row.coherence_impact_scalar) if row.coherence_impact_scalar is not None else "—",
                "chakra": row.primary_chakra or "—",
                "review": row.review_status or "—",
            })

        except Exception as exc:  # noqa: BLE001
            failures.append({"file": path.name, "error": str(exc)})
            logger.error("❌  %s — %s", path.name, exc)
            if not continue_on_error:
                raise

    return successes, failures


def _print_summary(successes: list[dict], failures: list[dict], dry_run: bool) -> None:
    mode = "DRY RUN — " if dry_run else ""
    print(f"\n{_hr()}")  # top border
    print(_row("File", "subject_id", "Status", "Alch. Stage", "Coh.", "Primary Chakra", "Review"))
    print(_hr())

    for s in successes:
        status = "✓ ok" + (" (dry)" if dry_run else "")
        print(_row(s["file"], s["subject_id"], status, s["alch_stage"], s["coherence"], s["chakra"], s["review"]))

    for f in failures:
        print(_row(f["file"], "—", "❌ fail", "—", "—", "—", "—"))

    print(_hr())
    total   = len(successes) + len(failures)
    ok_str  = f"✅ {len(successes)}/{total} imported" + (" (dry-run, no writes)" if dry_run else "")
    fail_str = f"  ❌ {len(failures)} failed" if failures else ""
    print(f"  {mode}{ok_str}{fail_str}")
    print(_hr())

    errs = get_validation_errors()
    if errs:
        print(f"\n  Validation error queue ({len(errs)} entries):")
        for i, e in enumerate(errs, 1):
            print(f"  [{i}] subject_id={e.get('subject_id')}  path={e.get('path')}")
            print(f"      {e.get('message', '')}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="GAIA-OS bulk crystal correspondence importer.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "directory",
        type=Path,
        help="Directory containing crystal JSON files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate all files against the schema but write nothing to the database.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search subdirectories recursively for .json files.",
    )
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue importing after per-file errors. Exit code 1 if any failed.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-file scalar extraction preview.",
    )
    parser.add_argument(
        "--db-url",
        default=os.environ.get("DATABASE_URL", ""),
        help="PostgreSQL connection string. Defaults to DATABASE_URL env var.",
    )
    args = parser.parse_args()

    if not args.directory.is_dir():
        logger.error("Directory not found: %s", args.directory)
        return 1

    files = _discover_files(args.directory, args.recursive)
    if not files:
        return 1

    mode_label = "DRY RUN — validating only" if args.dry_run else f"importing {len(files)} file(s)"
    print(f"\n  GAIA-OS Crystal Importer  |  {mode_label}")
    print(f"  directory : {args.directory.resolve()}")
    print(f"  files     : {len(files)}\n")

    clear_validation_errors()

    engine  = sa.create_engine(args.db_url, future=True)
    successes: list[dict] = []
    failures:  list[dict] = []

    with Session(engine) as session:
        with session.begin():
            try:
                successes, failures = _run_import(
                    files,
                    session,
                    dry_run=args.dry_run,
                    verbose=args.verbose,
                    continue_on_error=args.continue_on_error,
                )
                if args.dry_run:
                    session.rollback()
                elif failures and not args.continue_on_error:
                    session.rollback()
            except Exception:
                session.rollback()
                _print_summary(successes, failures, args.dry_run)
                return 1

    _print_summary(successes, failures, args.dry_run)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
