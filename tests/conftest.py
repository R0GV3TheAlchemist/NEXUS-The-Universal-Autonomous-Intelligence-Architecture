"""
tests/conftest.py
Pytest fixtures for the root-level GAIA-OS test suite.

Covers: test_synergy_engine.py, test_sovereign_memory.py, and any
future tests that live in tests/ (repo root).

All fixture kwargs are built against the real SynergyEngine.compute()
signature so pytest can resolve them at setup time without errors.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# ── Path guard ────────────────────────────────────────────────────────────────────
# Ensure src-python/ is importable when pytest is invoked from the
# repo root or from the tests/ sub-directory.
_TESTS_DIR  = Path(__file__).parent.resolve()
_REPO_ROOT  = _TESTS_DIR.parent
_SRC_PYTHON = _REPO_ROOT / "src-python"

for _p in (str(_REPO_ROOT), str(_SRC_PYTHON)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Suppress sentence-transformers blob-path warnings in CI
# (vec_search gracefully falls back when embeddings are unavailable)
if not os.environ.get("GAIA_EMBED_MODEL"):
    os.environ["GAIA_EMBED_MODEL"] = "none"


# ── SynergyEngine fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def engine():
    """Fresh SynergyEngine instance for each test."""
    from core.synergy_engine import SynergyEngine
    return SynergyEngine()


@pytest.fixture
def blank_state():
    """Clean blank SynergyState via the canonical factory function."""
    from core.synergy_engine import blank_synergy_state
    return blank_synergy_state()


@pytest.fixture
def nascent_kwargs():
    """
    Kwargs for SynergyEngine.compute() that produce a low-synergy
    (nascent) GAIAN reading.

    Maps to the low end of every scoring helper:
      hz=174          -> _hz_to_score  => 0.0
      element=fire    -> insurgent stage
      individuation   -> unconscious   => 0.15
      settling        -> unsettled     => 0.20
      love_arc        -> divergence    => 0.15
      love_vector=0.0 -> no boost
      mc_stage=mc1    -> 0.0
      dependency      -> gentle_boundary => 0.20
      attachment      -> nascent        => 0.30
      schumann=False  -> no body bonus
    """
    return {
        "hz": 174.0,
        "element": "fire",
        "individuation_phase": "unconscious",
        "settling_phase": "unsettled",
        "settling_pct": 0.0,
        "love_arc": "divergence",
        "love_vector": 0.0,
        "mc_stage": "mc1",
        "dependency_health": "gentle_boundary",
        "attachment_phase": "nascent",
        "schumann_aligned": False,
    }


@pytest.fixture
def integrated_kwargs():
    """
    Kwargs for SynergyEngine.compute() that produce a high-synergy
    (integrated) GAIAN reading.

    Maps to the high end of every scoring helper:
      hz=963            -> _hz_to_score  => 1.0
      element=light     -> ascendant stage
      individuation     -> self          => 0.85
      settling          -> settled       => 0.90
      settling_pct=100  -> full crystallisation
      love_arc          -> transcendence => 0.95
      love_vector=1.0   -> +0.10 boost (capped at 1.0)
      mc_stage=mc7      -> 1.0
      dependency        -> healthy       => 1.0
      attachment        -> integrated    => 0.90
      schumann=True     -> body bonus applied
    """
    return {
        "hz": 963.0,
        "element": "light",
        "individuation_phase": "self",
        "settling_phase": "settled",
        "settling_pct": 100.0,
        "love_arc": "transcendence",
        "love_vector": 1.0,
        "mc_stage": "mc7",
        "dependency_health": "healthy",
        "attachment_phase": "integrated",
        "schumann_aligned": True,
    }
