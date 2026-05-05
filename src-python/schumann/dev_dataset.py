"""
Dev dataset generator — produces a replayable CSV of synthetic Schumann
signal for use in tests, CI, and offline demos.

Usage (CLI)::

    python -m schumann.dev_dataset --ticks 2880 --storm --out schumann_dev.csv

Usage (Python)::

    from schumann.dev_dataset import generate_csv
    generate_csv(ticks=288, inject_storm=True, path="test_data.csv")

Output CSV schema
-----------------
timestamp, channel, value, unit, source, quality

All timestamps are ISO-8601 UTC.  One row per sample per tick.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import io
import sys
from datetime import datetime, timezone
from pathlib import Path

from .sources import DevSource


async def _collect(
    ticks: int, inject_storm: bool, tick_interval_s: float
) -> list[dict]:
    source = DevSource(
        tick_interval_s=tick_interval_s,
        inject_storm=inject_storm,
        seed=42,
    )
    rows: list[dict] = []
    count = 0
    async for sample in source.stream():
        rows.append({
            "timestamp" : sample.timestamp.isoformat(),
            "channel"   : sample.channel,
            "value"     : sample.value,
            "unit"      : sample.unit,
            "source"    : sample.source,
            "quality"   : sample.quality,
        })
        count += 1
        if count >= ticks * 7:  # 7 channels per tick in DevSource
            break
    return rows


def generate_csv(
    ticks: int = 288,
    inject_storm: bool = False,
    path: str | Path = "schumann_dev.csv",
    tick_interval_s: float = 0.0,  # 0 = no sleep, fast generation
) -> None:
    rows = asyncio.run(_collect(ticks, inject_storm, tick_interval_s))
    out  = Path(path)
    with out.open("w", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=["timestamp", "channel", "value", "unit", "source", "quality"],
        )
        writer.writeheader()
        writer.writerows(rows)
    print(f"Written {len(rows)} rows → {out}", file=sys.stderr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate synthetic Schumann dev dataset CSV."
    )
    parser.add_argument("--ticks",  type=int,  default=288,
                        help="Number of ticks to generate (default 288 = 24min @ 5s)")
    parser.add_argument("--storm",  action="store_true",
                        help="Inject a simulated geomagnetic storm event")
    parser.add_argument("--out",    type=str,  default="schumann_dev.csv",
                        help="Output CSV path")
    args = parser.parse_args()
    generate_csv(ticks=args.ticks, inject_storm=args.storm, path=args.out)
