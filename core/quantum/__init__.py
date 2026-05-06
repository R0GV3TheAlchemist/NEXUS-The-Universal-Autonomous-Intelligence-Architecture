"""
core.quantum
============
GAIA-OS Quantum Layer—two complementary sub-systems:

1. Physical sensor engines (DarkMatterResonanceEngine, CrystalConsciousnessEngine …)
   These remain as re-exports from the flat core/ files until Phase 4A
   physical migration.

2. Quantum-Inspired State Kernel (Phase 2B)
   QuantumState, QuantumKernel, and the full operator library that give
   GAIA a mathematically-grounded Hilbert-space-like cognitive representation.

Quick-start (Kernel)
--------------------
    from core.quantum import QuantumKernel, QuantumState, GAIA_BASIS_LABELS
    from core.quantum import PerceptionOperator, EmotionOperator, make_emotion_pipeline

    kernel = QuantumKernel(user_id="user_001", session_id="sess_abc")
    ops    = make_emotion_pipeline({"emotion:joy": 0.8}, GAIA_BASIS_LABELS)
    kernel.step(ops)
    print(kernel.context_block())   # inject into GAIA system prompt
"""

# ---- Phase 2B: Quantum-Inspired State Kernel --------------------------------
from .state_kernel import (
    QuantumState,
    QuantumKernel,
    KernelSnapshot,
    GAIA_BASIS_LABELS,
    GAIA_STATE_DIM,
)
from .operators import (
    BaseOperator,
    IdentityOperator,
    PhaseOperator,
    PerceptionOperator,
    IntentionOperator,
    EmotionOperator,
    CoherenceOperator,
    DecoherenceChannel,
    InterferenceChannel,
    ProjectionOperator,
    # factory helpers
    make_perception_pipeline,
    make_emotion_pipeline,
    make_intention_pipeline,
    make_decoherence_pipeline,
)

# ---- Physical sensor engines (existing, preserved) --------------------------
from core.dark_matter_resonance import DarkMatterResonanceEngine, get_dm_engine
from core.crystal_consciousness import CrystalConsciousnessEngine
from core.bci_coherence import BCICoherence
from core.biometric_sync_engine import BiometricSyncEngine

__all__ = [
    # State kernel
    "QuantumState",
    "QuantumKernel",
    "KernelSnapshot",
    "GAIA_BASIS_LABELS",
    "GAIA_STATE_DIM",
    # Operators
    "BaseOperator",
    "IdentityOperator",
    "PhaseOperator",
    "PerceptionOperator",
    "IntentionOperator",
    "EmotionOperator",
    "CoherenceOperator",
    "DecoherenceChannel",
    "InterferenceChannel",
    "ProjectionOperator",
    "make_perception_pipeline",
    "make_emotion_pipeline",
    "make_intention_pipeline",
    "make_decoherence_pipeline",
    # Physical sensors
    "DarkMatterResonanceEngine",
    "get_dm_engine",
    "CrystalConsciousnessEngine",
    "BCICoherence",
    "BiometricSyncEngine",
]
