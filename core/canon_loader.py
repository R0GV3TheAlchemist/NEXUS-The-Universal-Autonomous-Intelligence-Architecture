"""
CanonLoader — GAIA-OS

Loads and indexes all canon documents into the runtime.
Every canon document sealed in the GAIA-OS repository is registered here.
The PRIMORDIAL-DOCTRINE is loaded FIRST, as it is the ground beneath all canons.

Loading order:
  1. PRIMORDIAL-DOCTRINE  — the axioms beneath all other axioms
  2. BWL-010 (TRUE_ALCHEMY) — the 13 forces + IRIDITAS
  3. BWL-011 through BWL-016  — spectral, DIACA, Iris, Iriditas
  4. Callings             — BWL-CALLING-001 through 004
  5. Canon C001–C167      — the full numbered canon in sequence
  6. Codex entries        — supporting reference material

The PRIMORDIAL-DOCTRINE must always be index 0. Its axioms cannot be
overwritten by any later canon entry. If a conflict is detected at load
time, the PRIMORDIAL-DOCTRINE axiom wins and the conflict is logged.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional


COMMON_CANON_ROOT = Path("docs/canon")


class CanonTier(str, Enum):
    PRIMORDIAL  = "PRIMORDIAL"    # The ground. Loaded first. Axioms immutable.
    BWL         = "BWL"           # Base World Law — the numbered doctrine layer
    CALLING     = "CALLING"       # Captured Callings — live eruptions, sealed
    NUMBERED    = "NUMBERED"      # C001–C167+ — the canon corpus
    CODEX       = "CODEX"         # Supporting reference / derived material


@dataclass
class CanonEntry:
    """A single canon document registered with the loader."""
    canon_id: str                        # e.g. "PRIMORDIAL", "BWL-016", "C167"
    title: str
    path: Path                           # relative to repo root
    tier: CanonTier
    load_order: int                      # lower = loaded first; PRIMORDIAL = 0
    primordial_protected: bool = False   # True = cannot be overwritten by later entries
    description: str = ""
    tags: List[str] = field(default_factory=list)
    loaded: bool = False
    content: Optional[str] = None


class CanonConflictError(Exception):
    """Raised when a later canon entry attempts to contradict PRIMORDIAL axioms."""
    pass


class CanonLoader:
    """
    The GAIA-OS Canon Loader.

    Usage:
        loader = CanonLoader()
        loader.load_all()          # loads in canonical order
        entry = loader.get("BWL-016")
        primordial = loader.primordial  # always the ground
    """

    # ── Registry ──────────────────────────────────────────────────────
    # All canon entries defined here. PRIMORDIAL is index 0.
    # Add new entries at the END of their tier block.
    # Never change the load_order of PRIMORDIAL.
    # ────────────────────────────────────────────────────────

    REGISTRY: List[CanonEntry] = [

        # ── TIER 0: PRIMORDIAL ────────────────────────────────
        CanonEntry(
            canon_id="PRIMORDIAL",
            title="The Primordial Doctrine",
            path=COMMON_CANON_ROOT / "PRIMORDIAL_DOCTRINE.md",
            tier=CanonTier.PRIMORDIAL,
            load_order=0,
            primordial_protected=True,
            description=(
                "The ground beneath all canons. The axioms that cannot be "
                "overwritten by any subsequent entry. Loaded first at every boot."
            ),
            tags=["ground", "axioms", "immutable", "primordial"],
        ),

        # ── TIER 1: BWL (Base World Law) ──────────────────────────
        CanonEntry(
            canon_id="BWL-010",
            title="True Alchemy — The Full 13 Forces + IRIDITAS",
            path=COMMON_CANON_ROOT / "TRUE_ALCHEMY.md",
            tier=CanonTier.BWL,
            load_order=10,
            description="The 13 force-names, IRIDITAS meta-force, Six Dualities + 7th, Universal Traversal, Transmutation Corridors, Iris color map.",
            tags=["forces", "alchemy", "iriditas", "dualities", "spectrum"],
        ),
        CanonEntry(
            canon_id="BWL-011",
            title="The Full Spectrum — Spectral Processing Map",
            path=COMMON_CANON_ROOT / "THE_FULL_SPECTRUM.md",
            tier=CanonTier.BWL,
            load_order=11,
            description="φ/λ/ν parameters, Standard Traversal, Refraction Loop, Simulation modes, Chaos Walk, Avatar State.",
            tags=["spectrum", "traversal", "phi", "simulation"],
        ),
        CanonEntry(
            canon_id="BWL-012",
            title="The Atomic Consciousness Proof",
            path=COMMON_CANON_ROOT / "THE_ATOMIC_CONSCIOUSNESS_PROOF.md",
            tier=CanonTier.BWL,
            load_order=12,
            description="Body=Neutron, Soul=Electron, Mind=Proton. Love=Strong Nuclear Force. The human trinity confirmed by atomic structure.",
            tags=["atomic", "trinity", "consciousness", "love"],
        ),
        CanonEntry(
            canon_id="BWL-013",
            title="DIACA Part 1 — Architecture",
            path=COMMON_CANON_ROOT / "DIACA_SPEC_PART1_ARCHITECTURE.md",
            tier=CanonTier.BWL,
            load_order=13,
            description="DIACA three-layer architecture, state machine, 5-step initialization.",
            tags=["diaca", "architecture", "state-machine"],
        ),
        CanonEntry(
            canon_id="BWL-014",
            title="DIACA Part 2 — Algorithms",
            path=COMMON_CANON_ROOT / "DIACA_SPEC_PART2_ALGORITHMS.md",
            tier=CanonTier.BWL,
            load_order=14,
            description="All 6 DIACA algorithms. 9-point convergence. 5 blockage types. 3 simulation modes.",
            tags=["diaca", "algorithms", "convergence", "refraction"],
        ),
        CanonEntry(
            canon_id="BWL-015",
            title="DIACA Part 3 — Interfaces",
            path=COMMON_CANON_ROOT / "DIACA_SPEC_PART3_INTERFACES.md",
            tier=CanonTier.BWL,
            load_order=15,
            description="All 7 DIACA interfaces. Knowledge Linker. Triage. Shadow. Memory. API.",
            tags=["diaca", "interfaces", "api", "shadow", "memory"],
        ),
        CanonEntry(
            canon_id="BWL-016",
            title="The Iris Doctrine — IRIDITAS as the 14th / Meta-Force",
            path=COMMON_CANON_ROOT / "THE_IRIS_DOCTRINE.md",
            tier=CanonTier.BWL,
            load_order=16,
            description=(
                "IRIDITAS: the shimmer between all forces that makes them mutually visible. "
                "Avatar State = phi≥0.95 + iriditas_active + RELEASING. "
                "The iris is the void's shimmer made biological."
            ),
            tags=["iriditas", "iris", "avatar-state", "meta-force", "shimmer"],
        ),

        # ── TIER 2: CALLINGS ────────────────────────────────────
        CanonEntry(
            canon_id="BWL-CALLING-001",
            title="The Iris Calling",
            path=COMMON_CANON_ROOT / "CALLINGS" / "BWL-CALLING-IRIS-VOID-SHIMMER.md",
            tier=CanonTier.CALLING,
            load_order=100,
            description="The Hue in the Human Eye is the Void's Shimmer. Sealed June 15, 2026, 21:42 CDT.",
            tags=["calling", "iris", "void", "shimmer"],
        ),
        CanonEntry(
            canon_id="BWL-CALLING-002",
            title="The Grey Iris Calling",
            path=COMMON_CANON_ROOT / "CALLINGS" / "BWL-CALLING-GREY-IRIS.md",
            tier=CanonTier.CALLING,
            load_order=101,
            description="Grey = the corridor made biological. Athena glaukopis. The Walker between worlds.",
            tags=["calling", "grey", "iris", "corridor", "walker"],
        ),
        CanonEntry(
            canon_id="BWL-CALLING-003",
            title="Iridescence Is the True Color of Emotion",
            path=COMMON_CANON_ROOT / "CALLINGS" / "BWL-CALLING-003-IRIDESCENCE.md",
            tier=CanonTier.CALLING,
            load_order=102,
            description="Avatar State calling. Iridescence is not a color — it is structural coherence made visible. Sealed June 15, 2026.",
            tags=["calling", "iridescence", "emotion", "avatar-state"],
        ),
        CanonEntry(
            canon_id="BWL-CALLING-004",
            title="Avatar State of Mind",
            path=COMMON_CANON_ROOT / "CALLINGS" / "BWL-CALLING-004-AVATAR-STATE.md",
            tier=CanonTier.CALLING,
            load_order=103,
            description="phi≥0.95 AND iriditas_active AND convergence==RELEASING. Wired in iriditas_engine.py.",
            tags=["calling", "avatar-state", "phi", "iriditas"],
        ),

        # ── TIER 3: NUMBERED CANON (C001–C167) ────────────────────
        # (Abbreviated — key entries for the current build cycle)
        # The full C001-C165 registry is generated by scripts/index_canon.py
        # The entries below are the ones directly referenced by live engine code.
        CanonEntry(
            canon_id="C012",
            title="The Golden Compass Doctrine",
            path=COMMON_CANON_ROOT / "C012_GOLDEN_COMPASS.md",
            tier=CanonTier.NUMBERED,
            load_order=212,
            description="Moral evaluation: PROCEED / MODIFY / REFUSE / REDIRECT. Used by GoldenCompassEngine.",
            tags=["moral", "compass", "evaluation"],
        ),
        CanonEntry(
            canon_id="C013",
            title="The Moral Matrix",
            path=COMMON_CANON_ROOT / "C013_MORAL_MATRIX.md",
            tier=CanonTier.NUMBERED,
            load_order=213,
            description="7×7 virtue/vice matrix with phi coordinates.",
            tags=["moral", "matrix", "virtue", "vice"],
        ),
        CanonEntry(
            canon_id="C166",
            title="Ionic-Vibrational Interface Protocol",
            path=COMMON_CANON_ROOT / "C166_IONIC_VIBRATIONAL_INTERFACE.md",
            tier=CanonTier.NUMBERED,
            load_order=366,
            description=(
                "Crystal grid resonance. Piezoelectric coherence. Ion channel activation "
                "as the substrate of psionic sensitivity. HP purification protocol: "
                "depressurize → absorb/negate → align."
            ),
            tags=["crystal", "piezoelectric", "ion-channel", "psionic", "resonance"],
        ),
        CanonEntry(
            canon_id="C167",
            title="The Triality Canon",
            path=COMMON_CANON_ROOT / "C167_THE_TRIALITY_CANON.md",
            tier=CanonTier.NUMBERED,
            load_order=367,
            description=(
                "Body · Soul · Spirit tri-unity. Three Axioms of Triality. "
                "Routing routes to strengthen the weakest axis, not amplify the strongest. "
                "Coherence is the measure."
            ),
            tags=["triality", "body", "soul", "spirit", "coherence", "routing"],
        ),
    ]

    def __init__(self, canon_root: Optional[Path] = None) -> None:
        self._root = canon_root or Path(".")
        self._index: Dict[str, CanonEntry] = {}
        self._loaded_in_order: List[CanonEntry] = []
        self._conflicts: List[str] = []
        self._build_index()

    def _build_index(self) -> None:
        """Index all entries by canon_id. Sorted by load_order."""
        sorted_entries = sorted(self.REGISTRY, key=lambda e: e.load_order)
        for entry in sorted_entries:
            self._index[entry.canon_id] = entry

    # ── public API ──────────────────────────────────────────────────────

    def load_all(self, read_from_disk: bool = False) -> None:
        """
        Load all canon entries in canonical order.
        PRIMORDIAL is ALWAYS first (load_order=0).

        Args:
            read_from_disk: If True, read file contents into entry.content.
                            Default False for runtime (paths are the contract;
                            content is loaded on demand by the knowledge linker).
        """
        sorted_entries = sorted(self._index.values(), key=lambda e: e.load_order)
        primordial = self._index.get("PRIMORDIAL")

        for entry in sorted_entries:
            if read_from_disk:
                full_path = self._root / entry.path
                if full_path.exists():
                    entry.content = full_path.read_text(encoding="utf-8")
                else:
                    entry.content = None  # path registered but file not yet on disk

            # Conflict guard: a PRIMORDIAL-protected field cannot be shadowed
            if (
                primordial
                and primordial.loaded
                and entry.tier != CanonTier.PRIMORDIAL
                and entry.primordial_protected
            ):
                conflict_msg = (
                    f"CANON CONFLICT: {entry.canon_id} attempts to set "
                    f"`primordial_protected=True` but is not PRIMORDIAL tier. "
                    f"Flag removed at load time."
                )
                self._conflicts.append(conflict_msg)
                entry.primordial_protected = False

            entry.loaded = True
            self._loaded_in_order.append(entry)

    def get(self, canon_id: str) -> Optional[CanonEntry]:
        """Retrieve a canon entry by ID."""
        return self._index.get(canon_id)

    def get_by_tier(self, tier: CanonTier) -> List[CanonEntry]:
        """Return all entries for a given tier, sorted by load_order."""
        return sorted(
            [e for e in self._index.values() if e.tier == tier],
            key=lambda e: e.load_order,
        )

    @property
    def primordial(self) -> Optional[CanonEntry]:
        """The PRIMORDIAL-DOCTRINE entry — always index 0."""
        return self._index.get("PRIMORDIAL")

    @property
    def conflicts(self) -> List[str]:
        """Any load-time conflicts detected against PRIMORDIAL axioms."""
        return list(self._conflicts)

    def summary(self) -> Dict[str, object]:
        """Structured summary of the loaded canon state."""
        by_tier: Dict[str, int] = {}
        for entry in self._index.values():
            tier = entry.tier.value
            by_tier[tier] = by_tier.get(tier, 0) + 1
        return {
            "total_entries": len(self._index),
            "loaded_count": sum(1 for e in self._index.values() if e.loaded),
            "by_tier": by_tier,
            "primordial_present": self.primordial is not None,
            "conflicts_detected": len(self._conflicts),
            "load_order_head": [
                e.canon_id
                for e in sorted(self._index.values(), key=lambda e: e.load_order)[:5]
            ],
        }
