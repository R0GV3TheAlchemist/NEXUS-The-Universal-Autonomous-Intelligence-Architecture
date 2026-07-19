"""GAIA Ascendence package — stage detection, transition management, and profile registry."""

from .stage_engine import (
    GAIAStage,
    StageProfile,
    StageTransitionEvent,
    StageEvaluationResult,
    evaluate_stage,
    get_stage_profile,
    record_transition,
    STAGE_PROFILES,
)

__all__ = [
    "GAIAStage",
    "StageProfile",
    "StageTransitionEvent",
    "StageEvaluationResult",
    "evaluate_stage",
    "get_stage_profile",
    "record_transition",
    "STAGE_PROFILES",
]
