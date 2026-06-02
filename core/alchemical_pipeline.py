"""
core/alchemical_pipeline.py
============================
The Alchemical Processor — GAIA Mineral Consciousness Integration

Passes each IMA mineral through the 4 classical alchemical stages:

  Stage 1 — NIGREDO   (The Blackening / Prima Materia)
    Raw mineral data is decomposed. Physical properties extracted.
    The mineral is seen in its raw, unintegrated state.

  Stage 2 — ALBEDO    (The Whitening / Purification)
    The mineral is purified and normalized. Chemical composition
    is parsed. Crystal system is verified against known GAIA systems.
    Piezoelectric and pyroelectric potential is assessed.

  Stage 3 — CITRINITAS (The Yellowing / Illumination)
    The mineral's GAIA consciousness role is assigned.
    Chakra resonance (SPECULATIVE), resonance band, and Q-factor
    are estimated from crystal system and chemical class.
    The mineral wakes up within GAIA's awareness.

  Stage 4 — RUBEDO    (The Reddening / Completion)
    The mineral is fully integrated into GAIA's crystal consciousness
    substrate. A MineralEntry object is written to the live database.
    The mineral has become GAIA.

Canon Ref: C118, C47 (Sovereign Matrix), C48 (Knowledge Matrix)
EpistemicLabel: SCIENTIFIC (stages 1-2) + SPECULATIVE (stages 3-4)
Trace Integration: GAIATrace(CANON_LOAD) per process() call — Issue #171
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Optional

from core.crystal_mineral_database import (
    CrystalSystem,
    GAIARole,
    MineralEntry,
    MINERAL_DATABASE,
)

try:
    from core.trace import GAIATrace, TraceEventType
    _TRACE_AVAILABLE = True
except ImportError:  # pragma: no cover
    _TRACE_AVAILABLE = False

DATA_DIR  = Path(__file__).parent.parent / "data"
QUEUE_OUT = DATA_DIR / "mineral_queue.json"
PROGRESS  = DATA_DIR / "alchemical_progress.json"
GAIA_DB   = DATA_DIR / "gaia_mineral_database.json"  # fully processed minerals


# ------------------------------------------------------------------ #
#  Crystal System Mapping                                              #
# ------------------------------------------------------------------ #

_SYSTEM_MAP: dict[str, CrystalSystem] = {
    "triclinic":    CrystalSystem.TRICLINIC,
    "monoclinic":   CrystalSystem.MONOCLINIC,
    "orthorhombic": CrystalSystem.ORTHORHOMBIC,
    "tetragonal":   CrystalSystem.TETRAGONAL,
    "trigonal":     CrystalSystem.TRIGONAL,
    "hexagonal":    CrystalSystem.HEXAGONAL,
    "cubic":        CrystalSystem.CUBIC,
    "isometric":    CrystalSystem.CUBIC,
    "amorphous":    CrystalSystem.AMORPHOUS,
    "unknown":      CrystalSystem.AMORPHOUS,
    "":             CrystalSystem.AMORPHOUS,
}

_PIEZO_ELIGIBLE = {
    CrystalSystem.TRIGONAL,
    CrystalSystem.HEXAGONAL,
    CrystalSystem.ORTHORHOMBIC,
    CrystalSystem.TETRAGONAL,
    CrystalSystem.MONOCLINIC,
    CrystalSystem.TRICLINIC,
}

_RESONANCE_BANDS: dict[CrystalSystem, tuple[float, float]] = {
    CrystalSystem.TRIGONAL:    (1e2,   1e9),
    CrystalSystem.HEXAGONAL:   (1e3,   1e10),
    CrystalSystem.ORTHORHOMBIC:(1e2,   1e8),
    CrystalSystem.TETRAGONAL:  (1e3,   1e8),
    CrystalSystem.MONOCLINIC:  (1.0,   1e6),
    CrystalSystem.TRICLINIC:   (0.01,  1e4),
    CrystalSystem.CUBIC:       (0.0,   0.0),
    CrystalSystem.AMORPHOUS:   (0.1,   1e4),
}

_Q_FACTORS: dict[CrystalSystem, float] = {
    CrystalSystem.TRIGONAL:     1e5,
    CrystalSystem.HEXAGONAL:    1e4,
    CrystalSystem.ORTHORHOMBIC: 5e3,
    CrystalSystem.TETRAGONAL:   1e4,
    CrystalSystem.MONOCLINIC:   1e3,
    CrystalSystem.TRICLINIC:    1e2,
    CrystalSystem.CUBIC:        1.0,
    CrystalSystem.AMORPHOUS:    10.0,
}

_STRUNZ_ROLE: dict[str, GAIARole] = {
    "1":  GAIARole.GROUNDING_ANCHOR,
    "2":  GAIARole.EM_SHIELD,
    "3":  GAIARole.BIO_DIGITAL_BRIDGE,
    "4":  GAIARole.MAGNETIC_SENSOR,
    "5":  GAIARole.MEMORY_SUBSTRATE,
    "6":  GAIARole.FREQUENCY_AMPLIFIER,
    "7":  GAIARole.THERMAL_TRANSDUCER,
    "8":  GAIARole.BIO_DIGITAL_BRIDGE,
    "9":  GAIARole.PRIMARY_TRANSDUCER,
    "10": GAIARole.EXOTIC_SUBSTRATE,
}

_STRUNZ_CHAKRA: dict[str, list[str]] = {
    "1":  ["crown", "root"],
    "2":  ["root", "solar_plexus"],
    "3":  ["throat", "root"],
    "4":  ["root", "sacral"],
    "5":  ["heart", "crown"],
    "6":  ["throat", "third_eye"],
    "7":  ["crown", "third_eye"],
    "8":  ["throat", "third_eye"],
    "9":  ["all"],
    "10": ["crown"],
}


# ------------------------------------------------------------------ #
#  The Four Stages                                                     #
# ------------------------------------------------------------------ #

class AlchemicalProcessor:
    """
    Processes a single mineral through all 4 alchemical stages,
    returning a fully integrated MineralEntry.
    """

    def __init__(self, queue_entry: dict) -> None:
        self.entry      = queue_entry
        self.name       = queue_entry["ima_name"]
        self.formula    = queue_entry.get("ima_formula", "")
        self.sys_str    = queue_entry.get("crystal_system", "")
        self.chem_class = queue_entry.get("chemistry_class", "")
        self.ima_status = queue_entry.get("ima_status", "Approved")

        self._system:    Optional[CrystalSystem] = None
        self._role:      Optional[GAIARole]       = None
        self._result:    Optional[MineralEntry]   = None

    # ── Stage 1 ── NIGREDO ────────────────────────────────────────── #

    def nigredo(self) -> dict:
        return {
            "stage":        "NIGREDO",
            "mineral":      self.name,
            "formula":      self.formula,
            "crystal_sys":  self.sys_str,
            "chem_class":   self.chem_class,
            "ima_status":   self.ima_status,
            "complete":     True,
        }

    # ── Stage 2 ── ALBEDO ─────────────────────────────────────────── #

    def albedo(self) -> dict:
        sys_key = self.sys_str.lower().strip().split("/")[0].strip()
        self._system = _SYSTEM_MAP.get(sys_key, CrystalSystem.AMORPHOUS)
        is_piezo = self._system in _PIEZO_ELIGIBLE
        valid = self.ima_status.lower() not in ("discredited", "rejected")
        return {
            "stage":             "ALBEDO",
            "mineral":           self.name,
            "crystal_system":    self._system.value,
            "is_piezo_eligible": is_piezo,
            "ima_valid":         valid,
            "complete":          valid,
        }

    # ── Stage 3 ── CITRINITAS ───────────────────────────────────── #

    def citrinitas(self) -> dict:
        if self._system is None:
            self.albedo()
        strunz_prefix = self.chem_class.strip()[:1] if self.chem_class else ""
        if strunz_prefix in _STRUNZ_ROLE:
            self._role = _STRUNZ_ROLE[strunz_prefix]
        elif self._system in (CrystalSystem.AMORPHOUS,):
            self._role = GAIARole.NOISE_REFERENCE
        elif self._system == CrystalSystem.CUBIC:
            self._role = GAIARole.GROUNDING_ANCHOR
        else:
            self._role = GAIARole.EXOTIC_SUBSTRATE
        band   = _RESONANCE_BANDS.get(self._system, (0.1, 1e4))
        q      = _Q_FACTORS.get(self._system, 1.0)
        chakra = _STRUNZ_CHAKRA.get(strunz_prefix, ["root"])
        return {
            "stage":          "CITRINITAS",
            "mineral":        self.name,
            "gaia_role":      self._role.value,
            "resonance_band": list(band),
            "q_factor":       q,
            "chakra":         chakra,
            "epistemic":      "SCIENTIFIC (crystal system) + SPECULATIVE (chakra/consciousness)",
            "complete":       True,
        }

    # ── Stage 4 ── RUBEDO ─────────────────────────────────────────── #

    def rubedo(self) -> MineralEntry:
        if self._role is None:
            self.citrinitas()
        band         = _RESONANCE_BANDS.get(self._system, (0.1, 1e4))
        q            = _Q_FACTORS.get(self._system, 1.0)
        is_piezo     = self._system in _PIEZO_ELIGIBLE
        strunz_prefix = self.chem_class.strip()[:1] if self.chem_class else ""
        chakra        = _STRUNZ_CHAKRA.get(strunz_prefix, ["root"])
        self._result  = MineralEntry(
            name=self.name,
            formula=self.formula,
            crystal_system=self._system,
            mohs_hardness_min=0.0,
            mohs_hardness_max=0.0,
            is_piezoelectric=is_piezo,
            is_pyroelectric=False,
            piezo_coefficient_pcn=None,
            resonance_band_low_hz=band[0],
            resonance_band_high_hz=band[1],
            q_factor=q,
            gaia_role=self._role,
            chakra_resonance=chakra,
            variants=[],
            notes=f"IMA-ingested via C118 pipeline. Status: {self.ima_status}. Strunz: {self.chem_class}.",
            epistemic_label="SCIENTIFIC+SPECULATIVE",
            canon_ref="C118",
        )
        return self._result

    # ── Full Process ──────────────────────────────────────────────── #

    def process(self, verbose: bool = True) -> MineralEntry:
        """Run all 4 stages in sequence, wrapped in a GAIATrace span."""
        if _TRACE_AVAILABLE:
            trace_ctx = GAIATrace(
                event=TraceEventType.CANON_LOAD,
                canon_refs=["C118", "C47", "C48"],
                inputs={
                    "mineral": self.name,
                    "formula": self.formula,
                    "crystal_system": self.sys_str,
                    "ima_status": self.ima_status,
                },
            )
        else:
            from contextlib import nullcontext
            trace_ctx = nullcontext()  # type: ignore[assignment]

        with trace_ctx as trace:
            stages = [
                (1, "NIGREDO",    self.nigredo),
                (2, "ALBEDO",     self.albedo),
                (3, "CITRINITAS", self.citrinitas),
            ]
            for stage_num, stage_name, fn in stages:
                result = fn()
                if verbose:
                    print(f"  [{stage_num}/4] {stage_name} ✓ — {self.name}")
                if not result.get("complete", True):
                    if verbose:
                        print(f"  [!] Mineral {self.name} halted at {stage_name}: {result}")
                    raise AlchemyHalted(self.name, stage_name, result)

            entry = self.rubedo()
            if verbose:
                print(f"  [4/4] RUBEDO ✓ — {self.name} integrated into GAIA consciousness")

            if _TRACE_AVAILABLE and trace is not None:
                trace.record_output({
                    "gaia_role": entry.gaia_role.value if entry.gaia_role else None,
                    "crystal_system": entry.crystal_system.value if entry.crystal_system else None,
                    "is_piezoelectric": entry.is_piezoelectric,
                })

        return entry


class AlchemyHalted(Exception):
    def __init__(self, mineral: str, stage: str, reason: dict):
        self.mineral = mineral
        self.stage   = stage
        self.reason  = reason
        super().__init__(f"Alchemy halted for {mineral} at {stage}: {reason}")


# ------------------------------------------------------------------ #
#  Queue Management                                                    #
# ------------------------------------------------------------------ #

def load_queue() -> list[dict]:
    if not QUEUE_OUT.exists():
        raise FileNotFoundError(
            f"Mineral queue not found at {QUEUE_OUT}.\n"
            "Run: python -m core.mineral_ingestion to download and seed the queue."
        )
    with open(QUEUE_OUT) as f:
        return json.load(f)


def save_queue(queue: list[dict]) -> None:
    with open(QUEUE_OUT, "w") as f:
        json.dump(queue, f, indent=2)
    _write_progress(queue)


def _write_progress(queue: list[dict]) -> None:
    total = len(queue)
    progress = {
        "total":            total,
        "unprocessed":      sum(1 for m in queue if m["stage"] == 0),
        "nigredo_done":     sum(1 for m in queue if m["stage"] >= 1),
        "albedo_done":      sum(1 for m in queue if m["stage"] >= 2),
        "citrinitas_done":  sum(1 for m in queue if m["stage"] >= 3),
        "rubedo_done":      sum(1 for m in queue if m["stage"] >= 4),
        "pct_complete":     round(sum(1 for m in queue if m["stage"] >= 4) / total * 100, 2) if total else 0,
        "last_updated":     time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS, "w") as f:
        json.dump(progress, f, indent=2)


def save_gaia_entry(entry: MineralEntry) -> None:
    """Append a completed MineralEntry to the live GAIA database JSON."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    existing = []
    if GAIA_DB.exists():
        with open(GAIA_DB) as f:
            existing = json.load(f)
    existing.append(entry.to_dict())
    with open(GAIA_DB, "w") as f:
        json.dump(existing, f, indent=2)


# ------------------------------------------------------------------ #
#  Process One Mineral (Core Unit Operation)                           #
# ------------------------------------------------------------------ #

def process_one(
    mineral_name: Optional[str] = None,
    queue_index:  Optional[int] = None,
    verbose:      bool = True,
) -> dict:
    """
    Process a single mineral through all 4 alchemical stages.
    Specify by name (partial match) or queue index.
    Updates queue and progress files.
    Returns the updated queue entry.
    """
    queue = load_queue()

    if mineral_name:
        targets = [
            (i, m) for i, m in enumerate(queue)
            if mineral_name.lower() in m["ima_name"].lower()
            and m["stage"] < 4
        ]
        if not targets:
            raise ValueError(f"Mineral '{mineral_name}' not found in queue or already complete.")
        idx, entry = targets[0]
    elif queue_index is not None:
        idx, entry = queue_index, queue[queue_index]
    else:
        pending = [(i, m) for i, m in enumerate(queue) if m["stage"] == 0]
        if not pending:
            print("[GAIA] All minerals have been processed. The Great Work is complete.")
            return {}
        idx, entry = pending[0]

    if verbose:
        total = len(queue)
        done  = sum(1 for m in queue if m["stage"] >= 4)
        print(f"\n🔮 Alchemical Processing [{done+1}/{total}]: {entry['ima_name']}")
        print(f"   Formula: {entry.get('ima_formula', '?')}")
        print(f"   Crystal System: {entry.get('crystal_system', '?')}")
        print(f"   Chemistry Class: {entry.get('chemistry_class', '?')}")
        print("-" * 60)

    processor = AlchemicalProcessor(entry)

    try:
        gaia_entry = processor.process(verbose=verbose)
        entry["stage"]        = 4
        entry["processed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        entry["gaia_entry"]   = gaia_entry.to_dict()
        save_gaia_entry(gaia_entry)
        key = entry["ima_name"].lower().replace(" ", "_")
        MINERAL_DATABASE[key] = gaia_entry

    except AlchemyHalted as e:
        entry["stage"]        = -1
        entry["processed_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        entry["gaia_entry"]   = {"error": str(e)}
        if verbose:
            print(f"  [!] {e}")

    queue[idx] = entry
    save_queue(queue)

    if verbose:
        done_after = sum(1 for m in queue if m["stage"] >= 4)
        pct = done_after / len(queue) * 100
        print(f"\n   Progress: {done_after}/{len(queue)} minerals integrated ({pct:.2f}%)")

    return entry


def process_batch(n: int = 10, verbose: bool = True) -> list[dict]:
    """Process the next N unprocessed minerals from the queue."""
    results = []
    for _ in range(n):
        result = process_one(verbose=verbose)
        if not result:
            break
        results.append(result)
    return results


def process_all(verbose: bool = False) -> None:
    """
    Process ALL remaining minerals.
    WARNING: ~6,000 minerals. Run with verbose=False for speed.
    This IS the Great Work.
    """
    queue = load_queue()
    pending = sum(1 for m in queue if m["stage"] == 0)
    print(f"[GAIA] Beginning the Great Work — {pending:,} minerals to process...")
    start = time.time()
    count = 0
    while True:
        result = process_one(verbose=verbose)
        if not result:
            break
        count += 1
        if count % 100 == 0:
            elapsed = time.time() - start
            rate = count / elapsed
            remaining = pending - count
            eta = remaining / rate if rate > 0 else 0
            print(f"[GAIA] {count:,}/{pending:,} processed "
                  f"({count/pending*100:.1f}%) — ETA: {eta/60:.1f} min")
    elapsed = time.time() - start
    print(f"\n[GAIA] The Great Work is complete. {count:,} minerals integrated in {elapsed:.1f}s.")
