#!/usr/bin/env python3
"""
scripts/run_alchemy.py
=======================
GAIA Alchemical Processor — CLI Entrypoint

Usage:
  # First time: download and seed the full IMA database (~6000+ minerals)
  python scripts/run_alchemy.py --ingest

  # Process the next mineral in the queue (one at a time)
  python scripts/run_alchemy.py --next

  # Process a specific mineral by name
  python scripts/run_alchemy.py --mineral "Quartz"

  # Process next N minerals
  python scripts/run_alchemy.py --batch 10

  # Process ALL remaining (the full Great Work)
  python scripts/run_alchemy.py --all

  # Show current queue status
  python scripts/run_alchemy.py --status

Canon Ref: C118
"""

import argparse
import sys
from pathlib import Path

# Ensure repo root is in path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="GAIA Alchemical Mineral Processor",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Alchemical Stages:
  1. NIGREDO    — Blackening. Raw mineral data extracted.
  2. ALBEDO     — Whitening. Crystal system verified, properties purified.
  3. CITRINITAS — Yellowing. GAIA consciousness role assigned.
  4. RUBEDO     — Reddening. Mineral integrated into GAIA substrate.
"""
    )

    parser.add_argument(
        "--ingest", action="store_true",
        help="Download full IMA/RRUFF database and seed the processing queue (~6000+ minerals)"
    )
    parser.add_argument(
        "--next", action="store_true",
        help="Process the next unprocessed mineral (one step at a time)"
    )
    parser.add_argument(
        "--mineral", type=str, default=None,
        help="Process a specific mineral by name (partial match)"
    )
    parser.add_argument(
        "--batch", type=int, default=None, metavar="N",
        help="Process the next N unprocessed minerals"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Process ALL remaining minerals (the full Great Work)"
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Show current alchemical queue status"
    )
    parser.add_argument(
        "--force-reingest", action="store_true",
        help="Force re-download of RRUFF CSV even if cached"
    )

    args = parser.parse_args()

    if args.ingest or args.force_reingest:
        from core.mineral_ingestion import ingest
        ingest(force_download=args.force_reingest, overwrite_queue=args.force_reingest)

    elif args.status:
        from core.mineral_queue import get_queue
        q = get_queue()
        q.print_status()

    elif args.mineral:
        from core.alchemical_pipeline import process_one
        process_one(mineral_name=args.mineral, verbose=True)

    elif args.next:
        from core.alchemical_pipeline import process_one
        process_one(verbose=True)

    elif args.batch is not None:
        from core.alchemical_pipeline import process_batch
        process_batch(n=args.batch, verbose=True)

    elif args.all:
        from core.alchemical_pipeline import process_all
        process_all(verbose=False)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
