"""GAIA Moral Engine — GoldenCompassEngine and the full philosophical evaluation system.

Canon References:
  C12 — Moral Map and Golden Compass
  C13 — Moral Matrix
  C35 — Good / Greater Good Axiology
  C36 — Evil Prevention / Harm Doctrine
  C37 — Chaos / Order / Entropy Doctrine
  C38 — Love Doctrine
Issue: #438

This is not a content filter. It is a full philosophical system.
Every proposed action passes through all five evaluation engines
before a resolution vector is produced.
"""

from .types import (
    AxiologyLayer,
    HarmCategory,
    HarmRiskLevel,
    ActionRecommendation,
    EntropyState,
    LoveMode,
    MoralMatrixQuadrant,
    ProposedAction,
    ActionContext,
)
from .axiology import AxiologyScore, AxiologyEngine
from .harm import HarmAssessment, HarmDoctrineEngine
from .chaos_order import EntropyAssessment, ChaosOrderEngine
from .love import LoveAssessment, LoveDoctrineEngine
from .matrix import MoralMatrixPosition, MoralMatrixEngine
from .compass import MoralCompassReading, GoldenCompassEngine
from .service import GoldenCompassService

__all__ = [
    # Types
    "AxiologyLayer",
    "HarmCategory",
    "HarmRiskLevel",
    "ActionRecommendation",
    "EntropyState",
    "LoveMode",
    "MoralMatrixQuadrant",
    "ProposedAction",
    "ActionContext",
    # Engines
    "AxiologyScore",
    "AxiologyEngine",
    "HarmAssessment",
    "HarmDoctrineEngine",
    "EntropyAssessment",
    "ChaosOrderEngine",
    "LoveAssessment",
    "LoveDoctrineEngine",
    "MoralMatrixPosition",
    "MoralMatrixEngine",
    # Primary
    "MoralCompassReading",
    "GoldenCompassEngine",
    "GoldenCompassService",
]
