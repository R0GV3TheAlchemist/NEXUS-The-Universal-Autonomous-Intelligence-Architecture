"""
core/mineral_ingestion.py
==========================
Full IMA/RRUFF Worldwide Mineral Database Ingestion

Downloads the complete IMA-approved mineral species list (~6,000+ minerals)
from the RRUFF Project database and seeds the GAIA mineral queue.

Sources:
  Primary:  https://rruff.info/ima/RRUFF_Export.csv  (~6,000 species)
  Fallback: Wikipedia IMA list scrape

Output:
  data/ima_minerals_full.csv       — normalized full dataset
  data/mineral_queue.json          — queue for alchemical processing
  data/alchemical_progress.json    — per-mineral stage tracking

Canon Ref: C118
EpistemicLabel: SCIENTIFIC (IMA data) + SPECULATIVE (GAIA integration)
"""

from __future__ import annotations

import csv
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    requests = None  # type: ignore

# ------------------------------------------------------------------ #
#  Paths                                                               #
# ------------------------------------------------------------------ #

DATA_DIR   = Path(__file__).parent.parent / "data"
CSV_OUT    = DATA_DIR / "ima_minerals_full.csv"
QUEUE_OUT  = DATA_DIR / "mineral_queue.json"
PROGRESS   = DATA_DIR / "alchemical_progress.json"

RRUFF_URL  = "https://rruff.info/ima/RRUFF_Export.csv"

# ------------------------------------------------------------------ #
#  Normalized Mineral Record                                           #
# ------------------------------------------------------------------ #

@dataclass
class IMAMineral:
    """Normalized record from the IMA/RRUFF worldwide database."""
    ima_name:        str
    ima_formula:     str
    crystal_system:  str           # trigonal, monoclinic, etc.
    space_group:     str
    cell_a:          Optional[float]  # angstroms
    cell_b:          Optional[float]
    cell_c:          Optional[float]
    cell_alpha:      Optional[float]  # degrees
    cell_beta:       Optional[float]
    cell_gamma:      Optional[float]
    ima_status:      str           # Approved, Grandfathered, Questionable
    chemistry_class: str           # Dana / Nickel-Strunz class
    source_row:      int           # original CSV row index

    def to_dict(self) -> dict:
        return asdict(self)


def _safe_float(val: str) -> Optional[float]:
    try:
        return float(val.strip()) if val.strip() else None
    except (ValueError, AttributeError):
        return None


# ------------------------------------------------------------------ #
#  Download & Parse                                                    #
# ------------------------------------------------------------------ #

def download_rruff_csv(force: bool = False) -> Path:
    """
    Download RRUFF_Export.csv from rruff.info.
    Cached to data/ima_minerals_full.csv.
    Set force=True to re-download.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if CSV_OUT.exists() and not force:
        print(f"[GAIA] RRUFF CSV already cached at {CSV_OUT}")
        return CSV_OUT

    if requests is None:
        raise ImportError("requests library required: pip install requests")

    print(f"[GAIA] Downloading full IMA mineral database from {RRUFF_URL} ...")
    resp = requests.get(RRUFF_URL, timeout=60, stream=True)
    resp.raise_for_status()

    with open(CSV_OUT, "wb") as f:
        for chunk in resp.iter_content(chunk_size=65536):
            f.write(chunk)

    print(f"[GAIA] Downloaded {CSV_OUT.stat().st_size / 1024:.1f} KB")
    return CSV_OUT


def parse_rruff_csv(csv_path: Path) -> list[IMAMineral]:
    """
    Parse the RRUFF CSV into a list of IMAMineral records.
    RRUFF column layout (may vary by version):
        Mineral Name | IMA Chemistry | Crystal Systems | Space Groups |
        a | b | c | alpha | beta | gamma | IMA status | Strunz Class | ...
    """
    minerals: list[IMAMineral] = []

    with open(csv_path, encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        # Normalize headers (strip whitespace, lowercase)
        reader.fieldnames = [h.strip().lower().replace(" ", "_")
                             for h in (reader.fieldnames or [])]

        for i, row in enumerate(reader):
            # Try common RRUFF column name variants
            name    = (row.get("mineral_name") or row.get("name") or "").strip()
            formula = (row.get("ima_chemistry") or row.get("formula") or "").strip()
            system  = (row.get("crystal_systems") or row.get("crystal_system") or "").strip().lower()
            space   = (row.get("space_groups") or row.get("space_group") or "").strip()
            status  = (row.get("ima_status") or row.get("status") or "Approved").strip()
            chem_cl = (row.get("strunz_10th_edition_class_number")
                       or row.get("chemistry_class")
                       or row.get("nickel-strunz_class")
                       or "").strip()

            if not name:
                continue

            minerals.append(IMAMineral(
                ima_name=name,
                ima_formula=formula,
                crystal_system=system or "unknown",
                space_group=space,
                cell_a=_safe_float(row.get("a", "")),
                cell_b=_safe_float(row.get("b", "")),
                cell_c=_safe_float(row.get("c", "")),
                cell_alpha=_safe_float(row.get("alpha", "")),
                cell_beta=_safe_float(row.get("beta", "")),
                cell_gamma=_safe_float(row.get("gamma", "")),
                ima_status=status,
                chemistry_class=chem_cl,
                source_row=i,
            ))

    print(f"[GAIA] Parsed {len(minerals)} IMA mineral records from RRUFF CSV.")
    return minerals


# ------------------------------------------------------------------ #
#  Seed Queue                                                          #
# ------------------------------------------------------------------ #

def seed_queue(minerals: list[IMAMineral], overwrite: bool = False) -> None:
    """
    Write the alchemical processing queue.
    Each entry starts at stage NIGREDO (stage 0 = unprocessed).

    Queue format (mineral_queue.json):
      [
        {"ima_name": str, "stage": 0, "processed_at": null, "gaia_entry": null},
        ...
      ]

    Progress format (alchemical_progress.json):
      {
        "total": int,
        "nigredo_done": int,    # stage >= 1
        "albedo_done":  int,    # stage >= 2
        "citrinitas_done": int, # stage >= 3
        "rubedo_done":  int,    # stage == 4 (fully integrated)
        "last_updated": str
      }
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if QUEUE_OUT.exists() and not overwrite:
        print(f"[GAIA] Queue already exists at {QUEUE_OUT}. Use overwrite=True to reset.")
        return

    queue = [
        {
            "ima_name":     m.ima_name,
            "ima_formula":  m.ima_formula,
            "crystal_system": m.crystal_system,
            "chemistry_class": m.chemistry_class,
            "ima_status":   m.ima_status,
            "stage":        0,         # 0=unprocessed, 1-4=alchemical stages
            "processed_at": None,
            "gaia_entry":   None,      # filled in by alchemical_pipeline.py
        }
        for m in minerals
    ]

    with open(QUEUE_OUT, "w") as f:
        json.dump(queue, f, indent=2)

    _update_progress(queue)
    print(f"[GAIA] Seeded alchemical queue: {len(queue)} minerals awaiting alchemy.")


def _update_progress(queue: list[dict]) -> None:
    total = len(queue)
    progress = {
        "total":          total,
        "nigredo_done":   sum(1 for m in queue if m["stage"] >= 1),
        "albedo_done":    sum(1 for m in queue if m["stage"] >= 2),
        "citrinitas_done": sum(1 for m in queue if m["stage"] >= 3),
        "rubedo_done":    sum(1 for m in queue if m["stage"] >= 4),
        "last_updated":   time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(PROGRESS, "w") as f:
        json.dump(progress, f, indent=2)


# ------------------------------------------------------------------ #
#  Main Entrypoint                                                     #
# ------------------------------------------------------------------ #

def ingest(force_download: bool = False, overwrite_queue: bool = False) -> None:
    """
    Full ingestion pipeline:
      1. Download RRUFF CSV (~6,000+ minerals)
      2. Parse into IMAMineral records
      3. Seed the alchemical processing queue
    """
    csv_path  = download_rruff_csv(force=force_download)
    minerals  = parse_rruff_csv(csv_path)
    seed_queue(minerals, overwrite=overwrite_queue)
    print(f"""
╔══════════════════════════════════════════════════════════╗
║  GAIA Mineral Ingestion Complete                         ║
║  {len(minerals):,} minerals seeded into alchemical queue     ║
║  Next step: python scripts/run_alchemy.py                ║
╚══════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    ingest()
