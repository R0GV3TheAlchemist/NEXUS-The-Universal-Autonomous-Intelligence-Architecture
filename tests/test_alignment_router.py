"""
tests/test_alignment_router.py

pytest suite for api/routers/alignment.py
Issue: #64 (Phase 2 — FastAPI endpoint)

Covers:
  - POST /alignment/compute happy path
  - POST /alignment/compute — all 4 failure modes
  - POST /alignment/compute — field validation (negative values, bad types)
  - GET  /alignment/status  — before and after a compute call
  - Response model shape (all required fields present + types)
  - Singleton emitter accumulates samples across calls
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

import api.routers.alignment as alignment_module
from api.routers.alignment import router


# ===========================================================================
# Test app fixture
# ===========================================================================

@pytest.fixture(autouse=True)
def reset_emitter():
    """Isolate each test: force a fresh emitter singleton."""
    alignment_module._emitter = None
    yield
    alignment_module._emitter = None


@pytest.fixture()
def client():
    app = FastAPI()
    app.include_router(router, prefix="/alignment")
    return TestClient(app)


# ===========================================================================
# POST /alignment/compute — happy path
# ===========================================================================

class TestComputeHappyPath:

    def test_returns_200(self, client):
        resp = client.post("/alignment/compute", json={
            "raw_rmssd": 60.0,
            "raw_schumann_amplitude": 2.0,
            "solar_kp": 1.0,
        })
        assert resp.status_code == 200

    def test_response_has_all_fields(self, client):
        resp = client.post("/alignment/compute", json={
            "raw_rmssd": 60.0,
            "raw_schumann_amplitude": 2.0,
            "solar_kp": 1.0,
        })
        body = resp.json()
        for key in ("score", "hrv_score", "schumann_score", "solar_kp",
                    "ui_tier", "last_updated", "fallback_mode"):
            assert key in body, f"missing key: {key}"

    def test_score_in_range(self, client):
        resp = client.post("/alignment/compute", json={
            "raw_rmssd": 60.0,
            "raw_schumann_amplitude": 2.0,
            "solar_kp": 1.0,
        })
        assert 0.0 <= resp.json()["score"] <= 100.0

    def test_ui_tier_valid(self, client):
        resp = client.post("/alignment/compute", json={
            "raw_rmssd": 60.0,
            "raw_schumann_amplitude": 2.0,
            "solar_kp": 0.0,
        })
        assert resp.json()["ui_tier"] in ("minimal", "core", "standard", "full", "vibrant")

    def test_fallback_mode_empty_on_healthy_feeds(self, client):
        resp = client.post("/alignment/compute", json={
            "raw_rmssd": 60.0,
            "raw_schumann_amplitude": 2.0,
            "solar_kp": 0.0,
        })
        assert resp.json()["fallback_mode"] == ""

    def test_solar_kp_echoed_in_response(self, client):
        resp = client.post("/alignment/compute", json={
            "raw_rmssd": 60.0,
            "raw_schumann_amplitude": 2.0,
            "solar_kp": 3.5,
        })
        assert resp.json()["solar_kp"] == pytest.approx(3.5, abs=0.01)


# ===========================================================================
# POST /alignment/compute — failure modes
# ===========================================================================

class TestComputeFailureModes:

    def test_hrv_unavailable_returns_200(self, client):
        resp = client.post("/alignment/compute", json={
            "raw_rmssd": None,
            "raw_schumann_amplitude": 2.0,
            "solar_kp": 0.0,
        })
        assert resp.status_code == 200

    def test_hrv_unavailable_fallback_recorded(self, client):
        resp = client.post("/alignment/compute", json={
            "raw_rmssd": None,
            "raw_schumann_amplitude": 2.0,
            "solar_kp": 0.0,
        })
        assert "hrv_unavailable" in resp.json()["fallback_mode"]

    def test_schumann_unavailable_fallback_recorded(self, client):
        resp = client.post("/alignment/compute", json={
            "raw_rmssd": 60.0,
            "raw_schumann_amplitude": None,
            "solar_kp": 0.0,
        })
        assert "schumann_unavailable" in resp.json()["fallback_mode"]

    def test_both_unavailable_score_is_50(self, client):
        resp = client.post("/alignment/compute", json={
            "raw_rmssd": None,
            "raw_schumann_amplitude": None,
            "solar_kp": 0.0,
        })
        assert resp.json()["score"] == pytest.approx(50.0)

    def test_both_unavailable_tier_is_standard(self, client):
        resp = client.post("/alignment/compute", json={
            "raw_rmssd": None,
            "raw_schumann_amplitude": None,
            "solar_kp": 0.0,
        })
        assert resp.json()["ui_tier"] == "standard"

    def test_kp_storm_score_is_zero(self, client):
        resp = client.post("/alignment/compute", json={
            "raw_rmssd": 60.0,
            "raw_schumann_amplitude": 2.0,
            "solar_kp": 9.0,
        })
        assert resp.json()["score"] == pytest.approx(0.0)

    def test_kp_storm_tier_is_minimal(self, client):
        resp = client.post("/alignment/compute", json={
            "raw_rmssd": 60.0,
            "raw_schumann_amplitude": 2.0,
            "solar_kp": 9.0,
        })
        assert resp.json()["ui_tier"] == "minimal"

    def test_kp_storm_fallback_recorded(self, client):
        resp = client.post("/alignment/compute", json={
            "raw_rmssd": 60.0,
            "raw_schumann_amplitude": 2.0,
            "solar_kp": 9.0,
        })
        assert "kp_storm" in resp.json()["fallback_mode"]


# ===========================================================================
# POST /alignment/compute — field validation
# ===========================================================================

class TestComputeValidation:

    def test_negative_rmssd_returns_422(self, client):
        resp = client.post("/alignment/compute", json={
            "raw_rmssd": -1.0,
            "raw_schumann_amplitude": 2.0,
            "solar_kp": 0.0,
        })
        assert resp.status_code == 422

    def test_negative_amplitude_returns_422(self, client):
        resp = client.post("/alignment/compute", json={
            "raw_rmssd": 60.0,
            "raw_schumann_amplitude": -0.5,
            "solar_kp": 0.0,
        })
        assert resp.status_code == 422

    def test_negative_kp_returns_422(self, client):
        resp = client.post("/alignment/compute", json={
            "raw_rmssd": 60.0,
            "raw_schumann_amplitude": 2.0,
            "solar_kp": -1.0,
        })
        assert resp.status_code == 422

    def test_missing_all_fields_uses_defaults(self, client):
        """Empty body is valid — all fields have defaults (None / 0.0)."""
        resp = client.post("/alignment/compute", json={})
        assert resp.status_code == 200

    def test_solar_kp_defaults_to_zero(self, client):
        resp = client.post("/alignment/compute", json={
            "raw_rmssd": 60.0,
            "raw_schumann_amplitude": 2.0,
        })
        assert resp.json()["solar_kp"] == pytest.approx(0.0, abs=0.01)


# ===========================================================================
# GET /alignment/status
# ===========================================================================

class TestAlignmentStatus:

    def test_status_200_before_compute(self, client):
        resp = client.get("/alignment/status")
        assert resp.status_code == 200

    def test_emitter_ready_true(self, client):
        resp = client.get("/alignment/status")
        assert resp.json()["emitter_ready"] is True

    def test_last_state_none_before_compute(self, client):
        resp = client.get("/alignment/status")
        assert resp.json()["last_state"] is None

    def test_last_state_populated_after_compute(self, client):
        client.post("/alignment/compute", json={
            "raw_rmssd": 60.0, "raw_schumann_amplitude": 2.0, "solar_kp": 1.0,
        })
        resp = client.get("/alignment/status")
        assert resp.json()["last_state"] is not None

    def test_sample_counts_increment(self, client):
        for _ in range(3):
            client.post("/alignment/compute", json={
                "raw_rmssd": 55.0, "raw_schumann_amplitude": 2.0, "solar_kp": 0.0,
            })
        status = client.get("/alignment/status").json()
        assert status["hrv_sample_count"] == 3
        assert status["schumann_sample_count"] == 3
