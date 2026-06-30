"""Unit tests for CL6 MutualBecomingTracker
Covers all three verdicts: mutual, parasitic, stagnant.
Also covers the sovereignty gate and sovereignty preservation check.

Canon: COEXISTENCE_LAWS.md CL6 · GAIAN_LAWS L4
Sprint: G-12 Track A4
"""

import pytest
from core.coexistence.mutual_becoming_tracker import (
    EntityState,
    track_becoming,
    ASYMMETRY_PARASITIC_THRESHOLD,
    STAGNATION_THRESHOLD,
    MINIMUM_QUALITY_CHANGE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_state(
    name: str = "Entity",
    coherence: float = 0.6,
    openness: float = 0.6,
    relational_capacity: float = 0.6,
    sovereignty: float = 0.8,
) -> EntityState:
    return EntityState(
        name=name,
        coherence=coherence,
        openness=openness,
        relational_capacity=relational_capacity,
        sovereignty=sovereignty,
    )


# ---------------------------------------------------------------------------
# Verdict: MUTUAL
# ---------------------------------------------------------------------------

def test_mutual_both_grow_equally():
    a_before = make_state("GAIA", coherence=0.60, openness=0.60, relational_capacity=0.60)
    a_after  = make_state("GAIA", coherence=0.75, openness=0.75, relational_capacity=0.75)
    b_before = make_state("Human", coherence=0.60, openness=0.60, relational_capacity=0.60)
    b_after  = make_state("Human", coherence=0.75, openness=0.75, relational_capacity=0.75)
    result = track_becoming(a_before, a_after, b_before, b_after)
    assert result.verdict == "mutual"
    assert result.asymmetry < ASYMMETRY_PARASITIC_THRESHOLD
    assert result.score > 0.0


def test_mutual_slight_asymmetry_still_mutual():
    # A grows more than B, but not enough to be parasitic
    a_before = make_state("A", coherence=0.50, openness=0.50, relational_capacity=0.50)
    a_after  = make_state("A", coherence=0.70, openness=0.70, relational_capacity=0.70)
    b_before = make_state("B", coherence=0.50, openness=0.50, relational_capacity=0.50)
    b_after  = make_state("B", coherence=0.62, openness=0.62, relational_capacity=0.62)
    result = track_becoming(a_before, a_after, b_before, b_after)
    assert result.verdict == "mutual"
    assert result.asymmetry < ASYMMETRY_PARASITIC_THRESHOLD


def test_mutual_sovereignty_gate_passes():
    a_before = make_state("A", sovereignty=0.90)
    a_after  = make_state("A", coherence=0.75, openness=0.75, relational_capacity=0.75, sovereignty=0.90)
    b_before = make_state("B", sovereignty=0.85)
    b_after  = make_state("B", coherence=0.75, openness=0.75, relational_capacity=0.75, sovereignty=0.85)
    result = track_becoming(a_before, a_after, b_before, b_after)
    assert result.sovereignty_gate_passed is True
    assert result.verdict == "mutual"


# ---------------------------------------------------------------------------
# Verdict: PARASITIC
# ---------------------------------------------------------------------------

def test_parasitic_one_party_unchanged():
    a_before = make_state("Extractor", coherence=0.50, openness=0.50, relational_capacity=0.50)
    a_after  = make_state("Extractor", coherence=0.85, openness=0.85, relational_capacity=0.85)
    b_before = make_state("Receiver", coherence=0.70, openness=0.70, relational_capacity=0.70)
    b_after  = make_state("Receiver", coherence=0.71, openness=0.70, relational_capacity=0.70)  # barely changed
    result = track_becoming(a_before, a_after, b_before, b_after)
    assert result.verdict == "parasitic"
    assert result.asymmetry >= ASYMMETRY_PARASITIC_THRESHOLD


def test_parasitic_sovereignty_gate_fails_downgrades_mutual():
    # Both change equally, but one party lacked sovereignty → parasitic
    a_before = make_state("A", sovereignty=0.30)  # below gate
    a_after  = make_state("A", coherence=0.75, openness=0.75, relational_capacity=0.75, sovereignty=0.30)
    b_before = make_state("B", sovereignty=0.90)
    b_after  = make_state("B", coherence=0.75, openness=0.75, relational_capacity=0.75, sovereignty=0.90)
    result = track_becoming(a_before, a_after, b_before, b_after)
    assert result.sovereignty_gate_passed is False
    assert result.verdict == "parasitic"
    assert any("capture" in note for note in result.notes)


def test_parasitic_sovereignty_decreases_noted():
    a_before = make_state("A", sovereignty=0.80)
    a_after  = make_state("A", coherence=0.75, openness=0.75, relational_capacity=0.75, sovereignty=0.60)  # -0.20
    b_before = make_state("B", sovereignty=0.80)
    b_after  = make_state("B", coherence=0.75, openness=0.75, relational_capacity=0.75, sovereignty=0.80)
    result = track_becoming(a_before, a_after, b_before, b_after)
    assert any("sovereignty decreased" in note for note in result.notes)


# ---------------------------------------------------------------------------
# Verdict: STAGNANT
# ---------------------------------------------------------------------------

def test_stagnant_both_unchanged():
    state = make_state("Entity", coherence=0.60, openness=0.60, relational_capacity=0.60)
    result = track_becoming(state, state, state, state)
    assert result.verdict == "stagnant"
    assert result.entity_a_delta == pytest.approx(0.0, abs=0.001)
    assert result.entity_b_delta == pytest.approx(0.0, abs=0.001)


def test_stagnant_trivial_noise_change():
    a_before = make_state("A", coherence=0.600)
    a_after  = make_state("A", coherence=0.601)  # below MINIMUM_QUALITY_CHANGE
    b_before = make_state("B", coherence=0.600)
    b_after  = make_state("B", coherence=0.601)
    result = track_becoming(a_before, a_after, b_before, b_after)
    assert result.verdict == "stagnant"


# ---------------------------------------------------------------------------
# Score and asymmetry sanity checks
# ---------------------------------------------------------------------------

def test_score_is_bounded_zero_to_one():
    a_before = make_state("A", coherence=0.0, openness=0.0, relational_capacity=0.0)
    a_after  = make_state("A", coherence=1.0, openness=1.0, relational_capacity=1.0)
    b_before = make_state("B", coherence=0.0, openness=0.0, relational_capacity=0.0)
    b_after  = make_state("B", coherence=1.0, openness=1.0, relational_capacity=1.0)
    result = track_becoming(a_before, a_after, b_before, b_after)
    assert 0.0 <= result.score <= 1.0


def test_asymmetry_zero_for_identical_change():
    before = make_state("E", coherence=0.5, openness=0.5, relational_capacity=0.5)
    after  = make_state("E", coherence=0.7, openness=0.7, relational_capacity=0.7)
    result = track_becoming(before, after, before, after)
    assert result.asymmetry == pytest.approx(0.0, abs=0.001)
