"""
core/five_forces_engine.py
===========================
Five Forces Engine — models the five primary dynamic forces shaping
every GAIAN interaction: attraction, repulsion, integration,
differentiation, and equilibrium.

Canon Ref: C22 — Dynamic Forces & Relational Flow Doctrine
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ForceVector:
    attraction:      float = 0.5
    repulsion:       float = 0.1
    integration:     float = 0.5
    differentiation: float = 0.3
    equilibrium:     float = 0.5
    doctrine_ref: str = "C22"

    def dominant_force(self) -> str:
        forces = {
            "attraction":      self.attraction,
            "repulsion":       self.repulsion,
            "integration":     self.integration,
            "differentiation": self.differentiation,
            "equilibrium":     self.equilibrium,
        }
        return max(forces, key=forces.__getitem__)

    def to_dict(self) -> dict:
        return {
            "attraction":      self.attraction,
            "repulsion":       self.repulsion,
            "integration":     self.integration,
            "differentiation": self.differentiation,
            "equilibrium":     self.equilibrium,
            "dominant_force":  self.dominant_force(),
            "doctrine_ref":    self.doctrine_ref,
        }


class FiveForcesEngine:
    """Computes the five dynamic force vector for a GAIAN turn."""

    def compute(
        self,
        bond_depth: float = 30.0,
        conflict_density: float = 0.3,
        coherence_phi: float = 0.5,
        synergy_factor: float = 0.5,
        fluidity_score: float = 0.5,
    ) -> ForceVector:
        attraction      = min(1.0, (bond_depth / 100.0) * 0.6 + synergy_factor * 0.4)
        repulsion       = min(1.0, conflict_density * 0.7 + (1.0 - coherence_phi) * 0.3)
        integration     = min(1.0, synergy_factor * 0.5 + coherence_phi * 0.5)
        differentiation = min(1.0, fluidity_score * 0.6 + (1.0 - synergy_factor) * 0.4)
        equilibrium     = min(1.0, (attraction + integration) / 2.0 * (1.0 - repulsion * 0.3))
        return ForceVector(
            attraction=round(attraction, 4),
            repulsion=round(repulsion, 4),
            integration=round(integration, 4),
            differentiation=round(differentiation, 4),
            equilibrium=round(equilibrium, 4),
        )
