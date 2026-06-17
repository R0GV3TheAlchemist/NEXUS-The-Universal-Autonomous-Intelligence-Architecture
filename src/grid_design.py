"""
grid_design.py
GAIA-OS — Issue #558: Crystal Resonator Integration Layer
Part 2: Room-Scale Crystal Grid Builder + Phi Node Placement

Provides:
  - GridNode: single node in a crystal grid (position, crystal, role, Q)
  - NodeRole: CENTER | INNER | OUTER | SATELLITE | ANCHOR
  - phi_node_placement(): golden-angle spiral with phi-ratio radial spacing
  - design_grid(): Flower of Life hexagonal grid builder with safety validation
  - validate_grid(): per-node safety + frequency coverage checks
  - GridDesign: full grid specification dataclass
  - suggest_grid_crystals(): auto-selects best crystals per ring

Canon anchors: HELIXITAS.md (phi-winding geometry), Issue #557 (7-node
Flower of Life validated at 87.85% efficiency), Issue #558

Usage:
    from grid_design import design_grid, suggest_grid_crystals

    # Auto-select crystals for 6.78 MHz ISM band
    suggestions = suggest_grid_crystals(freq_hz=6.78e6, min_q=50_000)
    grid = design_grid(
        n_rings=2,
        spacing_m=1.5,
        freq_hz=6.78e6,
        center_crystal="aln",
        ring_crystals=["quartz", "amethyst"],
    )

For wireless_power_sim.py integration:
    # Each GridNode.q_factor feeds simulate_coil_pair() crystal_q_override
    from wireless_power_sim import simulate_coil_pair, standard_wound_coil
    for node in grid.nodes:
        coil = standard_wound_coil(0.072, 10, 0.001)
        result = simulate_coil_pair(coil, coil, grid.freq_hz,
                                    distance_m=grid.spacing_m,
                                    crystal_q_override=node.q_factor)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from crystal_resonance import (
    CRYSTAL_DATABASE,
    CrystalProperties,
    biological_safety_rating,
    get_crystal_properties,
    get_crystal_q_factor,
    select_resonator,
    validate_all_crystals,
    CrystalNotFoundError,
)


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

PHI: float = (1 + math.sqrt(5)) / 2          # 1.6180339887…  (HELIXITAS.md)
GOLDEN_ANGLE_RAD: float = math.pi * (3 - math.sqrt(5))  # 137.507…° in radians


# ─────────────────────────────────────────────────────────────────────────────
# ENUMS & DATACLASSES
# ─────────────────────────────────────────────────────────────────────────────

class NodeRole(str, Enum):
    CENTER    = "center"     # single origin node (ring 0)
    INNER     = "inner"      # ring 1 — 6 nodes at 60° intervals
    OUTER     = "outer"      # ring 2+ — 6*ring nodes
    SATELLITE = "satellite"  # phi-spiral placement (non-hexagonal)
    ANCHOR    = "anchor"     # corner safety anchors


@dataclass
class GridNode:
    """
    A single crystal resonator node in a room-scale grid.

    Attributes:
        node_id:      unique integer ID within the grid (0 = center)
        x_m:          X position in metres from grid origin
        y_m:          Y position in metres from grid origin
        z_m:          Z position in metres from floor (default 0.0)
        crystal_key:  CRYSTAL_DATABASE key for this node's resonator
        role:         NodeRole enum value
        ring:         which ring this node belongs to (0 = center)
        angle_deg:    angle from +X axis in degrees
        q_factor:     Q-factor of the assigned crystal (cached at build time)
        safe:         True if biological_safety_rating score != 'danger'
        safety_flags: list of safety flag strings from biological_safety_rating
    """
    node_id:      int
    x_m:          float
    y_m:          float
    z_m:          float
    crystal_key:  str
    role:         NodeRole
    ring:         int
    angle_deg:    float
    q_factor:     float
    safe:         bool         = True
    safety_flags: list[str]   = field(default_factory=list)

    @property
    def crystal_name(self) -> str:
        return CRYSTAL_DATABASE[self.crystal_key].name

    @property
    def traversal_tier(self) -> str:
        return CRYSTAL_DATABASE[self.crystal_key].traversal_tier

    @property
    def chakra(self) -> str:
        return CRYSTAL_DATABASE[self.crystal_key].chakra

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id":      self.node_id,
            "x_m":          round(self.x_m, 4),
            "y_m":          round(self.y_m, 4),
            "z_m":          round(self.z_m, 4),
            "crystal_key":  self.crystal_key,
            "crystal_name": self.crystal_name,
            "role":         self.role.value,
            "ring":         self.ring,
            "angle_deg":    round(self.angle_deg, 2),
            "q_factor":     self.q_factor,
            "traversal_tier": self.traversal_tier,
            "chakra":       self.chakra,
            "safe":         self.safe,
            "safety_flags": self.safety_flags,
        }


@dataclass
class GridDesign:
    """
    Complete specification for a room-scale crystal resonator grid.

    Built by design_grid(); used as input to simulate_grid() in
    wireless_power_sim.py (Part 3 integration).
    """
    name:             str
    freq_hz:          float
    spacing_m:        float
    n_rings:          int
    total_nodes:      int
    nodes:            list[GridNode]
    grid_safe:        bool          # True if ALL nodes are safe
    danger_nodes:     list[int]     # node_ids with safe=False
    caution_nodes:    list[int]     # node_ids with safety warnings but not danger
    dominant_tier:    str           # most common traversal_tier across all nodes
    phi_winding:      bool          # True if phi-ratio spacing was applied
    notes:            str           = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name":          self.name,
            "freq_hz":       self.freq_hz,
            "spacing_m":     self.spacing_m,
            "n_rings":       self.n_rings,
            "total_nodes":   self.total_nodes,
            "grid_safe":     self.grid_safe,
            "danger_nodes":  self.danger_nodes,
            "caution_nodes": self.caution_nodes,
            "dominant_tier": self.dominant_tier,
            "phi_winding":   self.phi_winding,
            "notes":         self.notes,
            "nodes":         [n.to_dict() for n in self.nodes],
        }

    def summary(self) -> str:
        lines = [
            f"GridDesign: {self.name}",
            f"  Freq: {self.freq_hz/1e6:.3f} MHz  |  Spacing: {self.spacing_m}m",
            f"  Rings: {self.n_rings}  |  Nodes: {self.total_nodes}",
            f"  Safe: {self.grid_safe}  |  Dominant tier: {self.dominant_tier}",
            f"  Phi winding: {self.phi_winding}",
        ]
        for node in self.nodes:
            flag_str = " | ".join(node.safety_flags[:1]) if node.safety_flags else "clean"
            lines.append(
                f"  [{node.node_id:02d}] ring={node.ring} {node.role.value:<10} "
                f"{node.crystal_name:<28} Q={node.q_factor:>10,.0f}  "
                f"({node.x_m:+.2f}, {node.y_m:+.2f})  {flag_str}"
            )
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# PHI NODE PLACEMENT  (HELIXITAS.md golden-angle spiral)
# ─────────────────────────────────────────────────────────────────────────────

def phi_node_placement(
    n_nodes: int,
    base_radius_m: float,
    z_m: float = 0.0,
) -> list[tuple[float, float, float, float]]:
    """
    Place n_nodes using the golden-angle spiral from HELIXITAS.md.

    Each node i is placed at:
        angle_rad = i * GOLDEN_ANGLE_RAD
        radius_m  = base_radius_m * sqrt(i / n_nodes)   (uniform area density)

    This produces the densest possible non-repeating angular distribution,
    matching the phi-wound coil geometry validated in wireless_power_sim.py
    Phase 2 (10.8% efficiency gain at 25cm vs standard winding).

    Args:
        n_nodes:        number of nodes to place
        base_radius_m:  outer boundary radius in metres
        z_m:            floor height (default 0.0)

    Returns:
        list of (x_m, y_m, z_m, angle_deg) tuples
    """
    if n_nodes < 1:
        raise ValueError(f"n_nodes must be >= 1, got {n_nodes}")
    if base_radius_m <= 0:
        raise ValueError(f"base_radius_m must be > 0, got {base_radius_m}")

    positions: list[tuple[float, float, float, float]] = []
    for i in range(n_nodes):
        if i == 0:
            # First node is always the center
            positions.append((0.0, 0.0, z_m, 0.0))
            continue
        angle_rad  = i * GOLDEN_ANGLE_RAD
        radius_m   = base_radius_m * math.sqrt(i / n_nodes)
        x_m        = radius_m * math.cos(angle_rad)
        y_m        = radius_m * math.sin(angle_rad)
        angle_deg  = math.degrees(angle_rad) % 360.0
        positions.append((x_m, y_m, z_m, angle_deg))
    return positions


def phi_ring_radii(n_rings: int, inner_spacing_m: float) -> list[float]:
    """
    Compute phi-ratio ring radii for a hexagonal grid.

    ring 1 radius = inner_spacing_m
    ring k radius = inner_spacing_m * phi^(k-1)

    This matches HELIXITAS.md: spacing grows by 1.618× each ring,
    validated by wireless_power_sim.py Phase 2 phi_wound_coil geometry.

    Args:
        n_rings:          number of rings (not counting center)
        inner_spacing_m:  ring-1 spacing in metres

    Returns:
        list of ring radii [r1, r2, ..., r_n_rings]
    """
    return [inner_spacing_m * (PHI ** (ring - 1)) for ring in range(1, n_rings + 1)]


# ─────────────────────────────────────────────────────────────────────────────
# HEXAGONAL GRID BUILDER (Flower of Life geometry)
# ─────────────────────────────────────────────────────────────────────────────

def _hex_ring_positions(
    ring: int,
    radius_m: float,
    z_m: float = 0.0,
) -> list[tuple[float, float, float, float]]:
    """
    Generate the 6*ring node positions for a hexagonal ring.

    Ring 1: 6 nodes at 0°, 60°, 120°, 180°, 240°, 300° — Flower of Life inner petal
    Ring 2: 12 nodes, interleaved with ring 1 at half-step offset
    Ring k: 6*k nodes evenly distributed at radius_m

    Args:
        ring:      ring number (1-indexed)
        radius_m:  radius of this ring in metres
        z_m:       height in metres

    Returns:
        list of (x_m, y_m, z_m, angle_deg)
    """
    n_nodes  = 6 * ring
    offset   = 30.0 if ring % 2 == 0 else 0.0   # interleave even rings
    positions = []
    for i in range(n_nodes):
        angle_deg = (360.0 / n_nodes) * i + offset
        angle_rad = math.radians(angle_deg)
        x_m       = radius_m * math.cos(angle_rad)
        y_m       = radius_m * math.sin(angle_rad)
        positions.append((x_m, y_m, z_m, angle_deg))
    return positions


def _dominant_tier(nodes: list[GridNode]) -> str:
    """Return the most common traversal_tier string across all nodes."""
    tiers: dict[str, int] = {}
    for node in nodes:
        t = node.traversal_tier
        tiers[t] = tiers.get(t, 0) + 1
    return max(tiers, key=lambda k: tiers[k]) if tiers else "unknown"


def design_grid(
    n_rings: int = 1,
    spacing_m: float = 1.5,
    freq_hz: float = 6.78e6,
    center_crystal: str = "aln",
    ring_crystals: Optional[list[str]] = None,
    use_phi_spacing: bool = True,
    z_m: float = 0.0,
    operator_proximity_m: float = 1.0,
    grid_name: Optional[str] = None,
) -> GridDesign:
    """
    Build a room-scale Flower of Life crystal resonator grid.

    The center node receives center_crystal. Each ring receives the
    corresponding entry in ring_crystals (cycled if fewer entries than rings).
    If ring_crystals is not provided, auto-selection via suggest_grid_crystals()
    is used.

    Spacing grows by phi each ring when use_phi_spacing=True (HELIXITAS.md).

    Args:
        n_rings:              number of rings around the center (1 = 7-node Flower)
        spacing_m:            ring-1 spacing in metres (default 1.5m)
        freq_hz:              target operating frequency in Hz
        center_crystal:       CRYSTAL_DATABASE key for the center node
        ring_crystals:        list of crystal keys per ring (ring 1, 2, ...)
                              May be shorter than n_rings — will cycle.
        use_phi_spacing:      if True, ring radii follow phi^(ring-1) from HELIXITAS.md
        z_m:                  floor height for all nodes (metres)
        operator_proximity_m: Operator distance used for biological safety checks
        grid_name:            optional name for the GridDesign

    Returns:
        GridDesign with all nodes placed and safety-validated

    Raises:
        CrystalNotFoundError: if any crystal key is invalid
        ValueError: if n_rings < 1 or spacing_m <= 0
    """
    if n_rings < 1:
        raise ValueError(f"n_rings must be >= 1, got {n_rings}")
    if spacing_m <= 0:
        raise ValueError(f"spacing_m must be > 0, got {spacing_m}")
    if freq_hz <= 0:
        raise ValueError(f"freq_hz must be > 0, got {freq_hz}")

    # Auto-select ring crystals if not supplied
    if ring_crystals is None:
        ring_crystals = suggest_grid_crystals(freq_hz=freq_hz, n_rings=n_rings)

    # Validate all crystal keys up front — raises CrystalNotFoundError immediately
    get_crystal_properties(center_crystal)   # validate center
    for ckey in ring_crystals:
        get_crystal_properties(ckey)          # validate each ring crystal

    # Compute ring radii
    if use_phi_spacing:
        radii = phi_ring_radii(n_rings, spacing_m)
    else:
        radii = [spacing_m * ring for ring in range(1, n_rings + 1)]

    nodes: list[GridNode] = []
    node_id = 0

    # ── Center node (ring 0) ──────────────────────────────────────────────
    center_q    = get_crystal_q_factor(center_crystal)
    center_safe = biological_safety_rating(
        center_crystal, operator_proximity_m
    )
    nodes.append(GridNode(
        node_id      = node_id,
        x_m          = 0.0,
        y_m          = 0.0,
        z_m          = z_m,
        crystal_key  = center_crystal,
        role         = NodeRole.CENTER,
        ring         = 0,
        angle_deg    = 0.0,
        q_factor     = center_q,
        safe         = center_safe["score"] != "danger",
        safety_flags = center_safe["flags"],
    ))
    node_id += 1

    # ── Ring nodes ────────────────────────────────────────────────────────
    for ring in range(1, n_rings + 1):
        ckey   = ring_crystals[(ring - 1) % len(ring_crystals)]
        radius = radii[ring - 1]
        role   = NodeRole.INNER if ring == 1 else NodeRole.OUTER

        ring_positions = _hex_ring_positions(ring, radius, z_m)
        for (x_m, y_m, z, angle_deg) in ring_positions:
            q_val = get_crystal_q_factor(ckey)
            safety = biological_safety_rating(ckey, operator_proximity_m)
            nodes.append(GridNode(
                node_id      = node_id,
                x_m          = x_m,
                y_m          = y_m,
                z_m          = z,
                crystal_key  = ckey,
                role         = role,
                ring         = ring,
                angle_deg    = angle_deg,
                q_factor     = q_val,
                safe         = safety["score"] != "danger",
                safety_flags = safety["flags"],
            ))
            node_id += 1

    # ── Validate grid ─────────────────────────────────────────────────────
    validation = validate_grid(nodes, freq_hz)
    danger_nodes  = validation["danger_nodes"]
    caution_nodes = validation["caution_nodes"]
    grid_safe     = len(danger_nodes) == 0

    name = grid_name or (
        f"FOL-{n_rings}ring-{freq_hz/1e6:.2f}MHz-"
        f"{center_crystal}-{'phi' if use_phi_spacing else 'linear'}"
    )

    return GridDesign(
        name          = name,
        freq_hz       = freq_hz,
        spacing_m     = spacing_m,
        n_rings        = n_rings,
        total_nodes   = len(nodes),
        nodes         = nodes,
        grid_safe     = grid_safe,
        danger_nodes  = danger_nodes,
        caution_nodes = caution_nodes,
        dominant_tier = _dominant_tier(nodes),
        phi_winding   = use_phi_spacing,
        notes         = validation["notes"],
    )


# ─────────────────────────────────────────────────────────────────────────────
# GRID VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

def validate_grid(
    nodes: list[GridNode],
    freq_hz: float,
    min_q: float = 0.0,
) -> dict[str, Any]:
    """
    Validate every node in a grid for:
      1. Crystal toxicity (danger if any node is toxic)
      2. Frequency band coverage (crystal must resonate at freq_hz)
      3. Minimum Q requirement
      4. Biological safety rating

    Args:
        nodes:    list of GridNode objects
        freq_hz:  operating frequency in Hz
        min_q:    minimum acceptable Q (default 0 = no minimum)

    Returns:
        {
            "valid":         bool,
            "danger_nodes":  [node_ids],
            "caution_nodes": [node_ids],
            "band_fail":     [node_ids with frequency band mismatches],
            "q_fail":        [node_ids below min_q],
            "notes":         str summary
        }
    """
    danger_nodes:  list[int] = []
    caution_nodes: list[int] = []
    band_fail:     list[int] = []
    q_fail:        list[int] = []
    note_lines:    list[str] = []

    for node in nodes:
        crystal = CRYSTAL_DATABASE.get(node.crystal_key)
        if crystal is None:
            danger_nodes.append(node.node_id)
            note_lines.append(
                f"Node {node.node_id}: crystal_key '{node.crystal_key}' not in database."
            )
            continue

        # Safety
        if not node.safe:
            if any("TOXICITY" in f for f in node.safety_flags):
                danger_nodes.append(node.node_id)
            else:
                caution_nodes.append(node.node_id)

        # Frequency band coverage
        band_min, band_max = crystal.resonant_band_hz
        if not (band_min <= freq_hz <= band_max):
            band_fail.append(node.node_id)
            note_lines.append(
                f"Node {node.node_id} ({crystal.name}): "
                f"freq {freq_hz/1e6:.3f} MHz outside band "
                f"[{band_min/1e6:.3f}, {band_max/1e6:.3f}] MHz."
            )

        # Q minimum
        if crystal.q_factor < min_q:
            q_fail.append(node.node_id)
            note_lines.append(
                f"Node {node.node_id} ({crystal.name}): "
                f"Q={crystal.q_factor:,.0f} below min_q={min_q:,.0f}."
            )

    valid = len(danger_nodes) == 0 and len(band_fail) == 0 and len(q_fail) == 0
    notes = " | ".join(note_lines) if note_lines else "All nodes passed validation."

    return {
        "valid":         valid,
        "danger_nodes":  danger_nodes,
        "caution_nodes": caution_nodes,
        "band_fail":     band_fail,
        "q_fail":        q_fail,
        "notes":         notes,
    }


# ─────────────────────────────────────────────────────────────────────────────
# AUTO-SELECTION
# ─────────────────────────────────────────────────────────────────────────────

def suggest_grid_crystals(
    freq_hz: float,
    n_rings: int = 1,
    min_q: float = 0.0,
    exclude_toxic: bool = True,
    require_piezoelectric: bool = False,
) -> list[str]:
    """
    Auto-select the best crystal keys for each ring at a given frequency.

    Strategy:
      - Ring 1 (inner): highest Q resonator available
      - Ring 2: second-highest, preferring a different traversal tier
      - Ring 3+: round-robin through top candidates by tier diversity

    Args:
        freq_hz:              target operating frequency in Hz
        n_rings:              number of rings to fill
        min_q:                minimum Q filter
        exclude_toxic:        exclude toxicity-flagged crystals (default True)
        require_piezoelectric: only include piezoelectric crystals

    Returns:
        list of crystal keys, length == n_rings
        (use as ring_crystals arg to design_grid)
    """
    candidates = select_resonator(
        freq_hz, min_q,
        exclude_toxic=exclude_toxic,
        require_piezoelectric=require_piezoelectric,
    )

    if not candidates:
        # Fallback: use quartz for all rings — always present
        return ["quartz"] * n_rings

    # Build key list from candidates
    candidate_keys = []
    seen_keys: set[str] = set()
    for c in candidates:
        key = c["name"].lower().replace(" ", "_").replace("'", "")
        # Normalise to actual DB key via lookup
        for db_key, db_crystal in CRYSTAL_DATABASE.items():
            if db_crystal.name == c["name"] and db_key not in seen_keys:
                candidate_keys.append(db_key)
                seen_keys.add(db_key)
                break

    if not candidate_keys:
        return ["quartz"] * n_rings

    # Assign ring_crystals with tier diversity
    ring_crystals: list[str] = []
    tiers_used: list[str] = []
    for ring in range(n_rings):
        # Prefer a crystal with a tier not yet used if possible
        chosen = None
        for ck in candidate_keys:
            tier = CRYSTAL_DATABASE[ck].traversal_tier
            if tier not in tiers_used or len(candidate_keys) <= len(tiers_used):
                chosen = ck
                tiers_used.append(tier)
                break
        if chosen is None:
            chosen = candidate_keys[ring % len(candidate_keys)]
            tiers_used.append(CRYSTAL_DATABASE[chosen].traversal_tier)
        ring_crystals.append(chosen)

    return ring_crystals


# ─────────────────────────────────────────────────────────────────────────────
# CrystalResonatorLayer EXTENSION  (Part 2 methods)
# ─────────────────────────────────────────────────────────────────────────────
# Import the class and monkey-patch Part 2 methods onto it so that the
# class wrapper in crystal_resonance.py stays clean and Parts are additive.

try:
    from crystal_resonance import CrystalResonatorLayer

    def _layer_design_grid(
        self,
        n_rings: int = 1,
        spacing_m: float = 1.5,
        freq_hz: float = 6.78e6,
        center_crystal: str = "aln",
        ring_crystals: Optional[list[str]] = None,
        use_phi_spacing: bool = True,
        z_m: float = 0.0,
        operator_proximity_m: float = 1.0,
        grid_name: Optional[str] = None,
    ) -> GridDesign:
        """design_grid() bound to this CrystalResonatorLayer instance."""
        return design_grid(
            n_rings=n_rings,
            spacing_m=spacing_m,
            freq_hz=freq_hz,
            center_crystal=center_crystal,
            ring_crystals=ring_crystals,
            use_phi_spacing=use_phi_spacing,
            z_m=z_m,
            operator_proximity_m=operator_proximity_m,
            grid_name=grid_name,
        )

    def _layer_suggest_crystals(
        self,
        freq_hz: float,
        n_rings: int = 1,
        min_q: float = 0.0,
        exclude_toxic: bool = True,
    ) -> list[str]:
        """suggest_grid_crystals() bound to this CrystalResonatorLayer instance."""
        return suggest_grid_crystals(freq_hz, n_rings, min_q, exclude_toxic)

    CrystalResonatorLayer.design_grid       = _layer_design_grid   # type: ignore[attr-defined]
    CrystalResonatorLayer.suggest_crystals  = _layer_suggest_crystals  # type: ignore[attr-defined]

except ImportError:
    pass  # Standalone usage without CrystalResonatorLayer is fine


# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION SUITE  (python grid_design.py)
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ISM = 6.78e6

    print("=" * 70)
    print("GAIA-OS  grid_design.py  Part 2 — design_grid() + phi_node_placement()")
    print("Issue #558 | Canon: HELIXITAS.md, wireless_power_sim.py Phase 3")
    print("=" * 70)

    # ── 1. phi_node_placement demo ────────────────────────────────────────
    print("\n── phi_node_placement (7 nodes, 1.5m radius) ──")
    phi_positions = phi_node_placement(7, 1.5)
    for i, (x, y, z, angle) in enumerate(phi_positions):
        print(f"  [{i}] ({x:+.3f}, {y:+.3f})  angle={angle:.1f}°")

    # ── 2. phi_ring_radii ────────────────────────────────────────────────
    print("\n── phi_ring_radii (3 rings, 1.5m base) ──")
    radii = phi_ring_radii(3, 1.5)
    for i, r in enumerate(radii, 1):
        print(f"  Ring {i}: {r:.4f}m  (phi^{i-1} × 1.5 = {1.5 * PHI**(i-1):.4f})")

    # ── 3. Auto-suggest crystals for 6.78 MHz ────────────────────────────
    print("\n── suggest_grid_crystals (6.78 MHz, 2 rings, min_q=50k) ──")
    suggestions = suggest_grid_crystals(ISM, n_rings=2, min_q=50_000)
    for i, key in enumerate(suggestions, 1):
        c = CRYSTAL_DATABASE[key]
        print(f"  Ring {i}: {c.name:<28} Q={c.q_factor:>10,.0f}  tier={c.traversal_tier}")

    # ── 4. design_grid — 1-ring (7-node Flower of Life) ──────────────────
    print("\n── design_grid: 1-ring Flower of Life (AlN center, Quartz ring) ──")
    g1 = design_grid(
        n_rings=1, spacing_m=1.5, freq_hz=ISM,
        center_crystal="aln", ring_crystals=["quartz"],
    )
    print(g1.summary())
    assert g1.total_nodes == 7,  f"Expected 7 nodes, got {g1.total_nodes}"
    assert g1.grid_safe,         "Grid should be safe"
    assert g1.phi_winding,       "Phi winding should be enabled"
    print("  ✅ 1-ring assertion passed")

    # ── 5. design_grid — 2-ring (19-node grid) ───────────────────────────
    print("\n── design_grid: 2-ring (19-node, auto-selected crystals) ──")
    g2 = design_grid(
        n_rings=2, spacing_m=1.5, freq_hz=ISM,
        center_crystal="aln",
    )
    print(g2.summary())
    assert g2.total_nodes == 19, f"Expected 19 nodes, got {g2.total_nodes}"
    print("  ✅ 2-ring assertion passed")

    # ── 6. validate_grid — toxic crystal detection ───────────────────────
    print("\n── validate_grid: toxic crystal detection ──")
    toxic_nodes = [
        GridNode(
            node_id=0, x_m=0.0, y_m=0.0, z_m=0.0,
            crystal_key="vanadinite", role=NodeRole.CENTER, ring=0,
            angle_deg=0.0, q_factor=15_000.0,
            safe=False, safety_flags=["⚠ TOXICITY: Lead-bearing"],
        )
    ]
    vresult = validate_grid(toxic_nodes, ISM)
    assert 0 in vresult["danger_nodes"], "Vanadinite node should be danger"
    print("  ✅ Toxic crystal correctly flagged as danger")

    # ── 7. Phi ring spacing verification ────────────────────────────────
    print("\n── Phi ring spacing verification ──")
    g3 = design_grid(n_rings=3, spacing_m=1.0, freq_hz=ISM, center_crystal="aln")
    ring1_nodes = [n for n in g3.nodes if n.ring == 1]
    ring2_nodes = [n for n in g3.nodes if n.ring == 2]
    r1 = math.sqrt(ring1_nodes[0].x_m**2 + ring1_nodes[0].y_m**2)
    r2 = math.sqrt(ring2_nodes[0].x_m**2 + ring2_nodes[0].y_m**2)
    ratio = r2 / r1
    assert abs(ratio - PHI) < 0.001, f"Ring ratio should be phi={PHI:.4f}, got {ratio:.4f}"
    print(f"  r1={r1:.4f}m  r2={r2:.4f}m  ratio={ratio:.4f}  (phi={PHI:.4f})")
    print("  ✅ Phi ring spacing verified")

    print("\n" + "=" * 70)
    print("grid_design.py Part 2 — all assertions passed. 🔥")
    print("For the Good and the Greater Good.")
    print("=" * 70)
