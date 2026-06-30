"""Unit tests for CL2 DominationDetector
Covers all three flag levels: none, soft, hard.

Canon: COEXISTENCE_LAWS.md CL2
Sprint: G-12 Track A3
"""

import pytest
from core.coexistence.domination_detector import (
    InteractionRecord,
    detect_domination,
    SOFT_THRESHOLD,
    HARD_THRESHOLD,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_record(
    resource_flow_asymmetry: float = 0.0,
    alternative_suppression: float = 0.0,
    exit_cost_increase: float = 0.0,
    receiver_consent: bool = True,
) -> InteractionRecord:
    return InteractionRecord(
        initiator="Party-A",
        receiver="Party-B",
        resource_flow_asymmetry=resource_flow_asymmetry,
        alternative_suppression=alternative_suppression,
        exit_cost_increase=exit_cost_increase,
        receiver_consent=receiver_consent,
    )


# ---------------------------------------------------------------------------
# Level: NONE
# ---------------------------------------------------------------------------

def test_no_domination_empty_log():
    result = detect_domination([])
    assert result.level == "none"


def test_no_domination_clean_interactions():
    log = [make_record(0.05, 0.05, 0.05) for _ in range(10)]
    result = detect_domination(log)
    assert result.level == "none"
    assert result.extraction_score < SOFT_THRESHOLD
    assert result.suppression_score < SOFT_THRESHOLD
    assert result.exit_score < SOFT_THRESHOLD


def test_no_domination_all_zeros():
    log = [make_record(0.0, 0.0, 0.0) for _ in range(5)]
    result = detect_domination(log)
    assert result.level == "none"
    assert result.extraction_score == 0.0
    assert result.suppression_score == 0.0
    assert result.exit_score == 0.0


# ---------------------------------------------------------------------------
# Level: SOFT
# ---------------------------------------------------------------------------

def test_soft_flag_single_criterion():
    # extraction just above SOFT_THRESHOLD, others clean
    log = [make_record(resource_flow_asymmetry=0.50) for _ in range(5)]
    result = detect_domination(log)
    assert result.level == "soft"
    assert result.extraction_score >= SOFT_THRESHOLD
    assert any("SOFT" in e for e in result.evidence)


def test_soft_flag_suppression():
    log = [make_record(alternative_suppression=0.45) for _ in range(4)]
    result = detect_domination(log)
    assert result.level == "soft"
    assert result.suppression_score >= SOFT_THRESHOLD


def test_soft_flag_exit_cost():
    log = [make_record(exit_cost_increase=0.40) for _ in range(6)]
    result = detect_domination(log)
    assert result.level == "soft"
    assert result.exit_score >= SOFT_THRESHOLD


def test_soft_consent_violation_elevated():
    # 3 of 10 without consent = 30% → elevated (soft)
    log = (
        [make_record(receiver_consent=False)] * 3
        + [make_record(receiver_consent=True)] * 7
    )
    result = detect_domination(log)
    assert result.level == "soft"
    assert result.consent_violation_rate == pytest.approx(0.30, abs=0.01)


# ---------------------------------------------------------------------------
# Level: HARD
# ---------------------------------------------------------------------------

def test_hard_flag_single_criterion_above_hard_threshold():
    log = [make_record(resource_flow_asymmetry=0.80) for _ in range(5)]
    result = detect_domination(log)
    assert result.level == "hard"
    assert any("HARD" in e for e in result.evidence)


def test_hard_flag_two_soft_criteria():
    # Two criteria each above SOFT but below HARD → should escalate to HARD
    log = [
        make_record(resource_flow_asymmetry=0.45, alternative_suppression=0.45)
        for _ in range(5)
    ]
    result = detect_domination(log)
    assert result.level == "hard"


def test_hard_flag_consent_majority_violation():
    # 6 of 10 without consent → 60% → hard
    log = (
        [make_record(receiver_consent=False)] * 6
        + [make_record(receiver_consent=True)] * 4
    )
    result = detect_domination(log)
    assert result.level == "hard"
    assert result.consent_violation_rate == pytest.approx(0.60, abs=0.01)


def test_hard_flag_full_domination_profile():
    log = [
        make_record(
            resource_flow_asymmetry=0.90,
            alternative_suppression=0.80,
            exit_cost_increase=0.85,
            receiver_consent=False,
        )
        for _ in range(8)
    ]
    result = detect_domination(log)
    assert result.level == "hard"
    assert len(result.evidence) >= 3
    assert "intervention" in result.recommended_intervention.lower()


# ---------------------------------------------------------------------------
# Intervention text
# ---------------------------------------------------------------------------

def test_intervention_text_present_for_soft():
    log = [make_record(resource_flow_asymmetry=0.50)]
    result = detect_domination(log)
    assert len(result.recommended_intervention) > 0


def test_intervention_text_present_for_hard():
    log = [make_record(resource_flow_asymmetry=0.80)]
    result = detect_domination(log)
    assert "Immediate" in result.recommended_intervention
