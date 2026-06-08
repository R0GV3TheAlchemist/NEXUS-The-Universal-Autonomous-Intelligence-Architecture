"""
core/mineral_queue.py
======================
Mineral Queue — Persistent state for alchemical processing

Simple interface to inspect, navigate, and manage the
alchemical processing queue without loading the full pipeline.

Canon Ref: C118
"""

from __future__ import annotations

import json
from pathlib import Path

DATA_DIR  = Path(__file__).parent.parent / "data"
QUEUE_OUT = DATA_DIR / "mineral_queue.json"
PROGRESS  = DATA_DIR / "alchemical_progress.json"

ALCHEMICAL_STAGES = {
    -1: "HALTED (discredited/invalid)",
     0: "PRIMA MATERIA (unprocessed)",
     1: "NIGREDO (blackening — raw)",
     2: "ALBEDO (whitening — purified)",
     3: "CITRINITAS (yellowing — illuminated)",
     4: "RUBEDO (reddening — integrated into GAIA)",
}


class MineralQueue:
    """Read/write interface for the alchemical mineral queue."""

    def __init__(self) -> None:
        if not QUEUE_OUT.exists():
            raise FileNotFoundError(
                "Queue not initialized. Run: python -m core.mineral_ingestion"
            )
        with open(QUEUE_OUT) as f:
            self._queue: list[dict] = json.load(f)

    # ── Inspection ──────────────────────────────────────────────── #

    def status(self) -> dict:
        """Return overall progress summary."""
        q = self._queue
        total = len(q)
        done  = sum(1 for m in q if m["stage"] >= 4)
        return {
            "total":       total,
            "done":        done,
            "remaining":   total - done,
            "pct_done":    round(done / total * 100, 3) if total else 0,
            "by_stage":    {
                ALCHEMICAL_STAGES[s]: sum(1 for m in q if m["stage"] == s)
                for s in [-1, 0, 1, 2, 3, 4]
            }
        }

    def find(self, name: str) -> list[dict]:
        """Find minerals by partial name match."""
        return [m for m in self._queue if name.lower() in m["ima_name"].lower()]

    def next_pending(self, n: int = 5) -> list[dict]:
        """Return the next N unprocessed minerals."""
        return [m for m in self._queue if m["stage"] == 0][:n]

    def by_crystal_system(self, system: str) -> list[dict]:
        """Filter by crystal system."""
        return [m for m in self._queue if m.get("crystal_system", "").lower() == system.lower()]

    def integrated(self) -> list[dict]:
        """Return all minerals that have reached RUBEDO (fully integrated)."""
        return [m for m in self._queue if m["stage"] >= 4]

    def print_status(self) -> None:
        s = self.status()
        print(f"""
╔══════════════════════════════════════════════════════════╗
║  GAIA Alchemical Queue Status                            ║
╠══════════════════════════════════════════════════════════╣
║  Total minerals:     {s['total']:,:<37}║
║  Integrated (RUBEDO):{s['done']:,:<37}║
║  Remaining:          {s['remaining']:,:<37}║
║  Progress:           {s['pct_done']:.3f}%{'':<36}║
╠══════════════════════════════════════════════════════════╣""")
        for stage_name, count in s["by_stage"].items():
            if count > 0:
                print(f"║  {stage_name[:40]:<40}  {count:<5}║")
        print("╚══════════════════════════════════════════════════════════╝")


def get_queue() -> MineralQueue:
    return MineralQueue()
