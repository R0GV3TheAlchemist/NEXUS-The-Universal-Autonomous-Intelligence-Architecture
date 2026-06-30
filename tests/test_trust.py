"""
GAIA Tests — Trust + Adversarial Validation
Tests trust score dynamics, adversarial validation, and trust update loop.
Pure in-process — no network required.
"""

import pytest
from node.trust import TrustProfile
from network.adversary import AdversarialValidator
from network.trust_update import update_from_validation, trust_leaderboard


# --- TrustProfile tests ---

def test_baseline_score():
    p = TrustProfile("node-x")
    assert p.score == 0.5
    assert p.tier() == "NEUTRAL"

def test_accept_increases_score():
    p = TrustProfile("node-x")
    new_score = p.update_on_accept()
    assert new_score == 0.52
    assert p.history["accepted"] == 1

def test_reject_decreases_score_more():
    p = TrustProfile("node-x")
    new_score = p.update_on_reject()
    assert new_score == 0.45
    assert p.history["rejected"] == 1

def test_dispute_decreases_score():
    p = TrustProfile("node-x")
    new_score = p.update_on_dispute()
    assert new_score == 0.48

def test_score_clamped_to_bounds():
    p = TrustProfile("node-high", initial_score=0.99)
    p.update_on_accept()
    assert p.score == 1.0

    p2 = TrustProfile("node-low", initial_score=0.02)
    p2.update_on_reject()
    assert p2.score == 0.0

def test_tier_progression():
    p = TrustProfile("node-x", initial_score=0.9)
    assert p.tier() == "HIGHLY_TRUSTED"
    p2 = TrustProfile("node-y", initial_score=0.1)
    assert p2.tier() == "UNTRUSTED"


# --- AdversarialValidator tests ---

SAMPLE_CLAIM = {"id": "claim-abc", "statement": "GAIA is an epistemic OS", "confidence": 0.8}

SAMPLE_NODE_STATES = {
    "node-A": {"state": {"claim-abc": {"confidence": 0.82, "status": "supported"}}},
    "node-B": {"state": {"claim-abc": {"confidence": 0.75, "status": "supported"}}},
    "node-C": {"state": {"claim-abc": {"confidence": 0.20, "status": "disputed"}}},
}

def test_adversarial_challenge_votes():
    validator = AdversarialValidator()
    result = validator.challenge(SAMPLE_CLAIM, SAMPLE_NODE_STATES)
    # node-A and node-B: confidence > 0.65 → support
    # node-C: confidence < 0.35 → reject
    assert result.votes["support"] == 2
    assert result.votes["reject"]  == 1
    assert result.verdict == "network_supported"

def test_adversarial_uncertain_when_missing():
    validator = AdversarialValidator()
    claim = {"id": "nonexistent-claim", "statement": "Something unknown"}
    result = validator.challenge(claim, SAMPLE_NODE_STATES)
    # No node has this claim → all uncertain
    assert result.votes["uncertain"] == 3
    assert result.verdict == "network_contested"


# --- Trust update tests ---

def test_trust_update_on_supported_verdict():
    profile = TrustProfile("node-A")
    profiles = {"node-A": profile}

    validator = AdversarialValidator()
    result = validator.challenge(SAMPLE_CLAIM, SAMPLE_NODE_STATES)
    # result.verdict == "network_supported"

    update = update_from_validation("node-A", result, profiles)
    assert update["action"] == "accepted"
    assert update["delta"] > 0
    assert profile.score > 0.5

def test_leaderboard_ordering():
    profiles = {
        "node-A": TrustProfile("node-A", initial_score=0.9),
        "node-B": TrustProfile("node-B", initial_score=0.4),
        "node-C": TrustProfile("node-C", initial_score=0.7),
    }
    board = trust_leaderboard(profiles)
    assert board[0]["node_id"] == "node-A"
    assert board[1]["node_id"] == "node-C"
    assert board[2]["node_id"] == "node-B"
