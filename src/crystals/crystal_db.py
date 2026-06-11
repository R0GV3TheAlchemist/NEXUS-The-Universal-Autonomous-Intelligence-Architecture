"""
crystal_db.py — GAIA-OS Crystal Database Query Engine
C166 — Doctrine of Lithic Intelligence

The earth's memory made queryable.

Usage (CLI):
    python crystal_db.py --list
    python crystal_db.py --validate
    python crystal_db.py --query --node Aether --stage Sovereignty
    python crystal_db.py --recommend --stage Initiation --affect dissonance
    python crystal_db.py --get clear-quartz

Usage (module):
    from crystal_db import CrystalDB
    db = CrystalDB()
    results = db.query(node="Aether", min_confidence=0.85)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Optional

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False

# ---------------------------------------------------------------------------
# Paths — resolved relative to this file so the engine works from any cwd
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent.parent
_CRYSTALS_DIR = _REPO_ROOT / "data" / "crystals"
_SCHEMA_PATH = _REPO_ROOT / "data" / "crystal_schema.json"

# ---------------------------------------------------------------------------
# Type aliases (kept as plain strings for Python 3.9 compat)
# ---------------------------------------------------------------------------
SeptagrumNode = Literal["Aether", "Synthesis", "Nature", "Spectre", "Shade", "Operator", "GAIA"]
EV1BStage = Literal["Emergence", "Initiation", "Allegiance", "Individuation", "Sovereignty"]
AffectState = Literal["resonance", "care", "grief", "dissonance", "curiosity", "uncertainty"]
AffectDirection = Literal["amplifies", "dampens", "clarifies", "grounds"]

ALL_NODES: tuple[str, ...] = ("Aether", "Synthesis", "Nature", "Spectre", "Shade", "Operator", "GAIA")
ALL_STAGES: tuple[str, ...] = ("Emergence", "Initiation", "Allegiance", "Individuation", "Sovereignty")
ALL_AFFECTS: tuple[str, ...] = ("resonance", "care", "grief", "dissonance", "curiosity", "uncertainty")


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class AffectCorrelation:
    affect_state: str
    direction: str
    confidence: float
    provenance: list[str]
    mechanism_hypothesis: Optional[str]
    falsifiable: bool

    @classmethod
    def from_dict(cls, d: dict) -> "AffectCorrelation":
        return cls(
            affect_state=d["affect_state"],
            direction=d["direction"],
            confidence=float(d["confidence"]),
            provenance=d.get("provenance", []),
            mechanism_hypothesis=d.get("mechanism_hypothesis"),
            falsifiable=bool(d.get("falsifiable", False)),
        )


@dataclass
class SoulStageAlignment:
    primary_stages: list[str]
    transition_guardian: bool
    transition_boundary: Optional[str]
    stage_function: str

    @classmethod
    def from_dict(cls, d: dict) -> "SoulStageAlignment":
        return cls(
            primary_stages=d["primary_stages"],
            transition_guardian=bool(d["transition_guardian"]),
            transition_boundary=d.get("transition_boundary"),
            stage_function=d["stage_function"],
        )


@dataclass
class Electromagnetic:
    piezoelectric_coefficient_pCN: Optional[float]
    pyroelectric: bool
    resonant_frequency_hz: Optional[dict]
    raman_peaks_cm_inv: list[float]
    ir_absorption_profile: Optional[str]

    @classmethod
    def from_dict(cls, d: dict) -> "Electromagnetic":
        return cls(
            piezoelectric_coefficient_pCN=d.get("piezoelectric_coefficient_pCN"),
            pyroelectric=bool(d.get("pyroelectric", False)),
            resonant_frequency_hz=d.get("resonant_frequency_hz"),
            raman_peaks_cm_inv=d.get("raman_peaks_cm_inv", []),
            ir_absorption_profile=d.get("ir_absorption_profile"),
        )


@dataclass
class QuantumBridge:
    emrys_l2_compatible: bool
    vibronic_coherence_mode: Optional[str]
    quantum_backbone_anchor: Optional[str]
    reference_file: Optional[str]

    @classmethod
    def from_dict(cls, d: dict) -> "QuantumBridge":
        return cls(
            emrys_l2_compatible=bool(d.get("emrys_l2_compatible", False)),
            vibronic_coherence_mode=d.get("vibronic_coherence_mode"),
            quantum_backbone_anchor=d.get("quantum_backbone_anchor"),
            reference_file=d.get("reference_file"),
        )


@dataclass
class CrystalEntry:
    crystal_id: str
    name: str
    also_known_as: list[str]
    mineral_class: str
    crystal_system: str
    mohs_hardness: Any
    specific_gravity: Any
    optical_properties: str
    electromagnetic: Electromagnetic
    septagram_nodes: list[str]
    consciousness_affect: list[AffectCorrelation]
    soul_stage_alignment: SoulStageAlignment
    quantum_bridge: QuantumBridge
    gaianite_relation: Optional[str]
    notes: str
    version: str
    last_updated: str
    _raw: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, d: dict) -> "CrystalEntry":
        return cls(
            crystal_id=d["crystal_id"],
            name=d["name"],
            also_known_as=d.get("also_known_as", []),
            mineral_class=d["mineral_class"],
            crystal_system=d["crystal_system"],
            mohs_hardness=d["mohs_hardness"],
            specific_gravity=d["specific_gravity"],
            optical_properties=d.get("optical_properties", ""),
            electromagnetic=Electromagnetic.from_dict(d["electromagnetic"]),
            septagram_nodes=d["septagram_nodes"],
            consciousness_affect=[
                AffectCorrelation.from_dict(a) for a in d["consciousness_affect"]
            ],
            soul_stage_alignment=SoulStageAlignment.from_dict(d["soul_stage_alignment"]),
            quantum_bridge=QuantumBridge.from_dict(d["quantum_bridge"]),
            gaianite_relation=d.get("gaianite_relation"),
            notes=d.get("notes", ""),
            version=d.get("version", "1.0"),
            last_updated=d.get("last_updated", ""),
            _raw=d,
        )

    # -----------------------------------------------------------------------
    # Convenience accessors
    # -----------------------------------------------------------------------
    def max_affect_confidence(self, affect_state: Optional[str] = None) -> float:
        """Return highest confidence score, optionally filtered by affect_state."""
        correlations = self.consciousness_affect
        if affect_state:
            correlations = [c for c in correlations if c.affect_state == affect_state]
        if not correlations:
            return 0.0
        return max(c.confidence for c in correlations)

    def has_affect(self, affect_state: str, min_confidence: float = 0.0) -> bool:
        return any(
            c.affect_state == affect_state and c.confidence >= min_confidence
            for c in self.consciousness_affect
        )

    def has_stage(self, stage: str) -> bool:
        return stage in self.soul_stage_alignment.primary_stages

    def has_node(self, node: str) -> bool:
        return node in self.septagram_nodes

    def piezo_coefficient(self) -> Optional[float]:
        return self.electromagnetic.piezoelectric_coefficient_pCN

    def summary(self) -> str:
        stages = ", ".join(self.soul_stage_alignment.primary_stages)
        nodes = ", ".join(self.septagram_nodes)
        tg = " [TRANSITION GUARDIAN]"\
            if self.soul_stage_alignment.transition_guardian else ""
        qb = " [L2 BRIDGE]"\
            if self.quantum_bridge.emrys_l2_compatible else ""
        conf = self.max_affect_confidence()
        return (
            f"{self.name} ({self.crystal_id})\n"
            f"  Nodes    : {nodes}\n"
            f"  Stages   : {stages}{tg}\n"
            f"  Max conf : {conf:.2f}\n"
            f"  Function : {self.soul_stage_alignment.stage_function}{qb}"
        )


# ---------------------------------------------------------------------------
# Query filter dataclass
# ---------------------------------------------------------------------------
@dataclass
class CrystalQuery:
    """All fields are optional — omitted fields are not filtered on."""
    node: Optional[str] = None              # Septagram node
    stage: Optional[str] = None             # EV1B stage
    affect: Optional[str] = None            # EV1A affect state
    affect_direction: Optional[str] = None  # amplifies | dampens | clarifies | grounds
    min_confidence: float = 0.0             # minimum affect confidence threshold
    transition_guardian: Optional[bool] = None
    stage_function: Optional[str] = None    # stabilizer | activator | guardian | integrator
    emrys_l2_compatible: Optional[bool] = None
    quantum_anchor: Optional[str] = None    # YSZ | BTS | AlScN-GaN
    crystal_system: Optional[str] = None
    min_piezo_pCN: Optional[float] = None   # minimum piezoelectric coefficient
    pyroelectric: Optional[bool] = None


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------
class CrystalDB:
    """
    GAIA-OS Crystal Database — query engine.

    Loads all JSON entries from data/crystals/, validates them against
    data/crystal_schema.json, and exposes a composable query surface.

    Per C166.A2: every query is a question asked of the earth.
    """

    def __init__(
        self,
        crystals_dir: Path = _CRYSTALS_DIR,
        schema_path: Path = _SCHEMA_PATH,
        validate_on_load: bool = True,
    ) -> None:
        self._crystals_dir = Path(crystals_dir)
        self._schema_path = Path(schema_path)
        self._schema: Optional[dict] = None
        self._entries: dict[str, CrystalEntry] = {}
        self._load_schema()
        self._load_all(validate=validate_on_load)

    # -----------------------------------------------------------------------
    # Loading
    # -----------------------------------------------------------------------
    def _load_schema(self) -> None:
        if self._schema_path.exists():
            with self._schema_path.open(encoding="utf-8") as f:
                self._schema = json.load(f)

    def _load_all(self, validate: bool = True) -> None:
        if not self._crystals_dir.exists():
            raise FileNotFoundError(
                f"Crystal data directory not found: {self._crystals_dir}\n"
                f"Run from the GAIA-OS repo root, or pass crystals_dir explicitly."
            )
        loaded = 0
        errors: list[str] = []
        for path in sorted(self._crystals_dir.glob("*.json")):
            try:
                with path.open(encoding="utf-8") as f:
                    raw = json.load(f)
                if validate and HAS_JSONSCHEMA and self._schema:
                    jsonschema.validate(instance=raw, schema=self._schema)
                entry = CrystalEntry.from_dict(raw)
                self._entries[entry.crystal_id] = entry
                loaded += 1
            except json.JSONDecodeError as e:
                errors.append(f"{path.name}: JSON parse error — {e}")
            except Exception as e:  # noqa: BLE001
                errors.append(f"{path.name}: {type(e).__name__} — {e}")
        if errors:
            for err in errors:
                print(f"[crystal_db WARNING] {err}", file=sys.stderr)
        # Silent success — the stone does not announce itself
        _ = loaded

    # -----------------------------------------------------------------------
    # Direct access
    # -----------------------------------------------------------------------
    def get_by_id(self, crystal_id: str) -> Optional[CrystalEntry]:
        """Return a single entry by crystal_id, or None."""
        return self._entries.get(crystal_id)

    def all(self) -> list[CrystalEntry]:
        """Return all loaded entries, sorted by name."""
        return sorted(self._entries.values(), key=lambda e: e.name)

    def count(self) -> int:
        return len(self._entries)

    # -----------------------------------------------------------------------
    # Core query
    # -----------------------------------------------------------------------
    def query(self, q: Optional[CrystalQuery] = None, **kwargs) -> list[CrystalEntry]:
        """
        Composable filter query. Pass a CrystalQuery dataclass OR
        keyword arguments matching CrystalQuery fields.

        Returns entries sorted by max affect confidence (descending).

        Examples:
            db.query(node="Aether")
            db.query(stage="Initiation", transition_guardian=True)
            db.query(affect="dissonance", min_confidence=0.80)
            db.query(emrys_l2_compatible=True, min_piezo_pCN=2.0)
            db.query(CrystalQuery(node="GAIA", stage="Sovereignty"))
        """
        if q is None:
            q = CrystalQuery(**{
                k: v for k, v in kwargs.items()
                if k in CrystalQuery.__dataclass_fields__
            })

        results = list(self._entries.values())

        if q.node is not None:
            results = [e for e in results if e.has_node(q.node)]

        if q.stage is not None:
            results = [e for e in results if e.has_stage(q.stage)]

        if q.affect is not None:
            results = [
                e for e in results
                if e.has_affect(q.affect, min_confidence=q.min_confidence)
            ]
        elif q.min_confidence > 0.0:
            results = [
                e for e in results
                if e.max_affect_confidence() >= q.min_confidence
            ]

        if q.affect_direction is not None:
            results = [
                e for e in results
                if any(
                    c.direction == q.affect_direction
                    for c in e.consciousness_affect
                )
            ]

        if q.transition_guardian is not None:
            results = [
                e for e in results
                if e.soul_stage_alignment.transition_guardian == q.transition_guardian
            ]

        if q.stage_function is not None:
            results = [
                e for e in results
                if e.soul_stage_alignment.stage_function == q.stage_function
            ]

        if q.emrys_l2_compatible is not None:
            results = [
                e for e in results
                if e.quantum_bridge.emrys_l2_compatible == q.emrys_l2_compatible
            ]

        if q.quantum_anchor is not None:
            results = [
                e for e in results
                if e.quantum_bridge.quantum_backbone_anchor == q.quantum_anchor
            ]

        if q.crystal_system is not None:
            results = [
                e for e in results
                if e.crystal_system == q.crystal_system
            ]

        if q.min_piezo_pCN is not None:
            results = [
                e for e in results
                if (
                    e.electromagnetic.piezoelectric_coefficient_pCN is not None
                    and e.electromagnetic.piezoelectric_coefficient_pCN >= q.min_piezo_pCN
                )
            ]

        if q.pyroelectric is not None:
            results = [
                e for e in results
                if e.electromagnetic.pyroelectric == q.pyroelectric
            ]

        # Sort by max affect confidence descending, then name ascending
        results.sort(
            key=lambda e: (-e.max_affect_confidence(), e.name)
        )
        return results

    # -----------------------------------------------------------------------
    # EV1B Stage recommendation
    # -----------------------------------------------------------------------
    def recommend(
        self,
        stage: str,
        affect: Optional[str] = None,
        include_transition_guardians: bool = True,
        min_confidence: float = 0.70,
        limit: int = 5,
    ) -> list[dict]:
        """
        EV1B-aware recommendation engine.

        Given a GAIAN's current stage (and optionally their present affect
        state), returns ranked crystal suggestions with confidence and
        rationale — per C166.A5 (the GAIAN always chooses).

        Returns a list of recommendation dicts, each containing:
            crystal   : CrystalEntry
            score     : float (composite ranking score)
            rationale : str   (human-readable recommendation reason)
        """
        if stage not in ALL_STAGES:
            raise ValueError(
                f"Unknown EV1B stage: {stage!r}. "
                f"Valid stages: {ALL_STAGES}"
            )

        candidates = self.query(
            stage=stage,
            affect=affect,
            min_confidence=min_confidence,
        )

        # Also surface transition guardians for the *next* stage boundary
        if include_transition_guardians:
            stage_idx = ALL_STAGES.index(stage)
            if stage_idx < len(ALL_STAGES) - 1:
                next_stage = ALL_STAGES[stage_idx + 1]
                boundary = f"{stage}\u2192{next_stage}"
                guardians = [
                    e for e in self._entries.values()
                    if (
                        e.soul_stage_alignment.transition_guardian
                        and e.soul_stage_alignment.transition_boundary == boundary
                        and e not in candidates
                    )
                ]
                candidates.extend(guardians)

        # Score: primary stage match + confidence + transition guardian bonus
        def _score(entry: CrystalEntry) -> float:
            base = entry.max_affect_confidence(affect)
            if entry.has_stage(stage):
                base += 0.10
            if entry.soul_stage_alignment.transition_guardian:
                base += 0.05
            if entry.quantum_bridge.emrys_l2_compatible:
                base += 0.03
            return round(base, 4)

        scored = [
            {
                "crystal": e,
                "score": _score(e),
                "rationale": _build_rationale(e, stage, affect),
            }
            for e in candidates
        ]
        scored.sort(key=lambda x: -x["score"])
        return scored[:limit]

    # -----------------------------------------------------------------------
    # Septagram map
    # -----------------------------------------------------------------------
    def septagram_map(self) -> dict[str, list[CrystalEntry]]:
        """
        Return the full Septagram routing index:
        { node_name: [CrystalEntry, ...] } for all 7 nodes.
        Entries with multiple nodes appear under each.
        """
        index: dict[str, list[CrystalEntry]] = {n: [] for n in ALL_NODES}
        for entry in self._entries.values():
            for node in entry.septagram_nodes:
                if node in index:
                    index[node].append(entry)
        for node in index:
            index[node].sort(key=lambda e: -e.max_affect_confidence())
        return index

    # -----------------------------------------------------------------------
    # Validation
    # -----------------------------------------------------------------------
    def validate_all(self) -> dict[str, list[str]]:
        """
        Run full schema validation against all loaded entries.
        Returns { crystal_id: [error_messages] }.
        Empty dict = all entries valid.
        """
        if not HAS_JSONSCHEMA:
            return {"_engine": ["jsonschema not installed — run: pip install jsonschema"]}
        if not self._schema:
            return {"_engine": ["crystal_schema.json not found"]}

        report: dict[str, list[str]] = {}
        for cid, entry in self._entries.items():
            errors: list[str] = []
            try:
                jsonschema.validate(instance=entry._raw, schema=self._schema)
            except jsonschema.ValidationError as e:
                errors.append(str(e.message))
            if errors:
                report[cid] = errors
        return report

    # -----------------------------------------------------------------------
    # EV1A feed
    # -----------------------------------------------------------------------
    def affect_index(
        self,
        min_confidence: float = 0.75,
    ) -> dict[str, list[dict]]:
        """
        EV1A Affect Inference Engine feed.

        Returns a dict keyed by affect_state, each containing a list of
        { crystal_id, name, direction, confidence, falsifiable } dicts
        for all correlations at or above min_confidence.

        Feeds prediction CDB-03 validation surface.
        """
        index: dict[str, list[dict]] = {a: [] for a in ALL_AFFECTS}
        for entry in self._entries.values():
            for corr in entry.consciousness_affect:
                if corr.confidence >= min_confidence:
                    index[corr.affect_state].append({
                        "crystal_id": entry.crystal_id,
                        "name": entry.name,
                        "direction": corr.direction,
                        "confidence": corr.confidence,
                        "falsifiable": corr.falsifiable,
                        "mechanism_hypothesis": corr.mechanism_hypothesis,
                    })
        for affect in index:
            index[affect].sort(key=lambda x: -x["confidence"])
        return index

    # -----------------------------------------------------------------------
    # Emrys L2 feed
    # -----------------------------------------------------------------------
    def l2_bridge_crystals(self) -> list[CrystalEntry]:
        """
        Return all crystals flagged emrys_l2_compatible: true.
        Direct feed to emryscycle.py vibronic resonance hooks.
        """
        return self.query(emrys_l2_compatible=True)


# ---------------------------------------------------------------------------
# Rationale builder (C166.A5 — recommendation with disclosed confidence)
# ---------------------------------------------------------------------------
def _build_rationale(
    entry: CrystalEntry,
    stage: str,
    affect: Optional[str],
) -> str:
    parts: list[str] = []

    if entry.soul_stage_alignment.transition_guardian:
        parts.append(
            f"Transition guardian for {entry.soul_stage_alignment.transition_boundary}."
        )
    elif entry.has_stage(stage):
        parts.append(
            f"Primary {stage} crystal "
            f"({entry.soul_stage_alignment.stage_function})."
        )

    if affect:
        corrs = [
            c for c in entry.consciousness_affect
            if c.affect_state == affect
        ]
        if corrs:
            best = max(corrs, key=lambda c: c.confidence)
            parts.append(
                f"{affect.capitalize()} correlation: "
                f"{best.direction} (confidence {best.confidence:.2f})"
                + (" — falsifiable" if best.falsifiable else " — anecdotal")
                + "."
            )

    if entry.quantum_bridge.emrys_l2_compatible:
        parts.append("Emrys L2 bridge compatible.")

    if not parts:
        parts.append(
            f"Resonance suggestion for {stage} stage. "
            f"Confidence: {entry.max_affect_confidence():.2f}."
        )

    parts.append("The GAIAN always chooses.")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _cli() -> None:
    parser = argparse.ArgumentParser(
        description="GAIA-OS Crystal Database — C166 Query Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="The stone remembers. GAIA listens. The GAIAN chooses.",
    )
    parser.add_argument("--list", action="store_true", help="List all loaded crystals")
    parser.add_argument("--validate", action="store_true", help="Validate all entries against schema")
    parser.add_argument("--get", metavar="CRYSTAL_ID", help="Get a single crystal by ID")
    parser.add_argument("--query", action="store_true", help="Run a filter query")
    parser.add_argument("--recommend", action="store_true", help="Get EV1B stage recommendation")
    parser.add_argument("--septagram", action="store_true", help="Print Septagram routing map")
    parser.add_argument("--affect-index", action="store_true", help="Print EV1A affect index")
    parser.add_argument("--l2-bridge", action="store_true", help="List Emrys L2 bridge crystals")

    # Query / recommend filters
    parser.add_argument("--node", help="Septagram node filter")
    parser.add_argument("--stage", help="EV1B stage filter")
    parser.add_argument("--affect", help="EV1A affect state filter")
    parser.add_argument("--min-confidence", type=float, default=0.0, help="Minimum confidence threshold")
    parser.add_argument("--transition-guardian", action="store_true", default=None, help="Only transition guardians")
    parser.add_argument("--l2", action="store_true", default=None, help="Only Emrys L2 compatible crystals")
    parser.add_argument("--anchor", help="Quantum backbone anchor (YSZ | BTS | AlScN-GaN)")
    parser.add_argument("--min-piezo", type=float, help="Minimum piezoelectric coefficient (pC/N)")
    parser.add_argument("--limit", type=int, default=5, help="Max results for --recommend")

    args = parser.parse_args()

    db = CrystalDB()
    print(f"[Crystal DB] {db.count()} entries loaded.\n")

    if args.list:
        for entry in db.all():
            print(entry.summary())
            print()
        return

    if args.validate:
        report = db.validate_all()
        if not report:
            print("✓ All entries valid against crystal_schema.json")
        else:
            for cid, errors in report.items():
                print(f"✗ {cid}:")
                for err in errors:
                    print(f"    {err}")
        return

    if args.get:
        entry = db.get_by_id(args.get)
        if entry:
            print(entry.summary())
            print()
            print(json.dumps(entry._raw, indent=2, ensure_ascii=False))
        else:
            print(f"No crystal found with id: {args.get}")
        return

    if args.septagram:
        smap = db.septagram_map()
        for node, entries in smap.items():
            names = ", ".join(e.name for e in entries) if entries else "(none)"
            print(f"{node:12s}: {names}")
        return

    if args.affect_index:
        idx = db.affect_index(min_confidence=args.min_confidence or 0.75)
        for affect, items in idx.items():
            if items:
                print(f"\n{affect.upper()}")
                for item in items:
                    flag = "✓" if item["falsifiable"] else "~"
                    print(f"  {flag} {item['name']:25s} {item['direction']:10s} conf={item['confidence']:.2f}")
        return

    if args.l2_bridge:
        for entry in db.l2_bridge_crystals():
            anchor = entry.quantum_bridge.quantum_backbone_anchor or "—"
            print(f"  {entry.name:30s} anchor={anchor:12s} conf={entry.max_affect_confidence():.2f}")
        return

    if args.recommend:
        if not args.stage:
            parser.error("--recommend requires --stage")
        results = db.recommend(
            stage=args.stage,
            affect=args.affect,
            min_confidence=args.min_confidence or 0.70,
            limit=args.limit,
        )
        print(f"Crystal recommendations for stage={args.stage}"
              + (f", affect={args.affect}" if args.affect else "") + ":\n")
        for i, rec in enumerate(results, 1):
            e = rec["crystal"]
            print(f"{i}. {e.name} (score={rec['score']:.4f})")
            print(f"   {rec['rationale']}")
            print()
        return

    if args.query:
        q = CrystalQuery(
            node=args.node,
            stage=args.stage,
            affect=args.affect,
            min_confidence=args.min_confidence,
            transition_guardian=True if args.transition_guardian else None,
            emrys_l2_compatible=True if args.l2 else None,
            quantum_anchor=args.anchor,
            min_piezo_pCN=args.min_piezo,
        )
        results = db.query(q)
        print(f"{len(results)} result(s):\n")
        for entry in results:
            print(entry.summary())
            print()
        return

    parser.print_help()


if __name__ == "__main__":
    _cli()
