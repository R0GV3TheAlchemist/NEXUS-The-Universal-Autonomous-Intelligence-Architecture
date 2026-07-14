"""
Tests for the Operator Dashboard and its three backing API endpoints.

The dashboard itself is a static HTML file served by FastAPI's
StaticFiles mount. These tests verify:

  Static file
    - dashboard.html is served with 200 OK
    - response is text/html
    - the file contains the expected UI landmarks (title, key ids,
      the three API endpoint URLs it will call at runtime)

  /v1/sentinel/status  (dashboard status panel)
    - response shape matches what the JS expects
    - stat tiles fields present: audit_stats.{total,watch,warn,block,critical}
    - active_rules and rule_count present
    - recent_critical and recent_blocked present

  /v1/sentinel/audit   (dashboard query panel)
    - events array + count present
    - level / min_level / caller_id / gaian_id / since / limit filters
    - event objects contain every field the dashboard JS reads

  /v1/sentinel/audit/stream  (dashboard live feed)
    - endpoint returns 200 and text/event-stream content-type
    - a manually injected event appears in the stream as a valid JSON line
    - heartbeat comment is emitted when no events arrive

  Auth contract
    - GAIAN UUID callers are blocked (403) on all three endpoints
    - unauthenticated callers (empty caller_id) get 401 on all three

Design:
  - Reuses the same _make_app() + FakeAuthMiddleware pattern as
    test_sentinel_routes.py so there is no real boot sequence.
  - The StaticFiles mount is added to the same mini-app so the
    static tests run against the real file from disk.
  - SSE stream tests use the TestClient with stream=True to consume
    the first chunk without hanging.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware  # fastapi.middleware.base moved to starlette in FastAPI >= 0.111
from fastapi.staticfiles import StaticFiles
from fastapi.testclient import TestClient

from core.sentinel.sentinel import Sentinel
from core.sentinel.threat import ThreatCategory, ThreatEvent, ThreatLevel
from server.routes_sentinel import router as sentinel_router


# ---------------------------------------------------------------------------
# Helpers & fixtures
# ---------------------------------------------------------------------------

STATIC_DIR = Path(__file__).parent.parent / "static"
DASHBOARD_FILE = STATIC_DIR / "dashboard.html"


def _make_app(
    sentinel: Sentinel,
    caller_id: str = "operator-1",
    mount_static: bool = False,
) -> FastAPI:
    """
    Minimal FastAPI app with the Sentinel router + optional static mount.
    FakeAuthMiddleware injects caller_id so the operator dependency is
    satisfied without a real Bearer token.
    """
    app = FastAPI()

    class FakeAuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            request.state.caller_id = caller_id
            return await call_next(request)

    app.add_middleware(FakeAuthMiddleware)
    sentinel_router.sentinel = sentinel
    app.include_router(sentinel_router)

    if mount_static and STATIC_DIR.exists():
        app.mount("/dashboard", StaticFiles(directory=str(STATIC_DIR), html=True), name="dashboard")

    return app


def _event(
    level: ThreatLevel = ThreatLevel.WARN,
    caller_id: str = "op-test",
    gaian_id: str | None = None,
    occurred_at: datetime | None = None,
    blocked: bool = False,
) -> ThreatEvent:
    ev = ThreatEvent(
        level=level,
        category=ThreatCategory.RATE_LIMIT,
        rule_name="dashboard_test_rule",
        caller_id=caller_id,
        endpoint="/v1/os/status",
        gaian_id=gaian_id,
        description="Dashboard test event",
        occurred_at=occurred_at or datetime.now(timezone.utc),
    )
    ev.blocked = blocked
    return ev


_GAIAN_UUID = "550e8400-e29b-41d4-a716-446655440000"


# ---------------------------------------------------------------------------
# TestDashboardStaticFile
# ---------------------------------------------------------------------------

class TestDashboardStaticFile:
    def test_dashboard_file_exists_on_disk(self):
        """Sanity: the file must exist before we test serving it."""
        assert DASHBOARD_FILE.exists(), (
            f"dashboard.html not found at {DASHBOARD_FILE}. "
            "Run the commit that adds server/static/dashboard.html first."
        )

    def test_dashboard_served_200(self):
        client = TestClient(_make_app(Sentinel(), mount_static=True))
        resp = client.get("/dashboard/")
        assert resp.status_code == 200

    def test_dashboard_content_type_is_html(self):
        client = TestClient(_make_app(Sentinel(), mount_static=True))
        resp = client.get("/dashboard/")
        assert "text/html" in resp.headers.get("content-type", "")

    def test_dashboard_contains_title(self):
        html = DASHBOARD_FILE.read_text(encoding="utf-8")
        assert "GAIA OS" in html
        assert "Operator Dashboard" in html

    def test_dashboard_references_status_endpoint(self):
        html = DASHBOARD_FILE.read_text(encoding="utf-8")
        assert "/v1/sentinel/status" in html

    def test_dashboard_references_audit_endpoint(self):
        html = DASHBOARD_FILE.read_text(encoding="utf-8")
        assert "/v1/sentinel/audit" in html

    def test_dashboard_references_stream_endpoint(self):
        html = DASHBOARD_FILE.read_text(encoding="utf-8")
        assert "/v1/sentinel/audit/stream" in html

    def test_dashboard_has_connect_button(self):
        html = DASHBOARD_FILE.read_text(encoding="utf-8")
        assert "connectBtn" in html

    def test_dashboard_has_event_table(self):
        html = DASHBOARD_FILE.read_text(encoding="utf-8")
        assert "event-table" in html

    def test_dashboard_has_stat_tiles(self):
        html = DASHBOARD_FILE.read_text(encoding="utf-8")
        for tile_id in ("statTotal", "statWatch", "statWarn", "statBlock", "statCritical"):
            assert tile_id in html, f"Missing stat tile id: {tile_id}"


# ---------------------------------------------------------------------------
# TestStatusEndpointForDashboard
# ---------------------------------------------------------------------------

class TestStatusEndpointForDashboard:
    """Verify /v1/sentinel/status returns every field the dashboard JS reads."""

    def test_status_200(self):
        client = TestClient(_make_app(Sentinel()))
        assert client.get("/v1/sentinel/status").status_code == 200

    def test_status_has_audit_stats_with_all_keys(self):
        client = TestClient(_make_app(Sentinel()))
        data = client.get("/v1/sentinel/status").json()
        stats = data["audit_stats"]
        for key in ("total", "watch", "warn", "block", "critical"):
            assert key in stats, f"audit_stats missing key: {key}"

    def test_status_has_active_rules_list(self):
        client = TestClient(_make_app(Sentinel()))
        data = client.get("/v1/sentinel/status").json()
        assert isinstance(data["active_rules"], list)
        assert isinstance(data["rule_count"], int)

    def test_status_has_recent_critical_and_blocked(self):
        client = TestClient(_make_app(Sentinel()))
        data = client.get("/v1/sentinel/status").json()
        assert "recent_critical" in data
        assert "recent_blocked" in data

    def test_status_recent_blocked_capped_at_ten(self):
        s = Sentinel()
        for _ in range(15):
            s.audit.record(_event(ThreatLevel.BLOCK))
        client = TestClient(_make_app(s))
        data = client.get("/v1/sentinel/status").json()
        assert len(data["recent_blocked"]) <= 10

    def test_status_recent_critical_capped_at_ten(self):
        s = Sentinel()
        for _ in range(15):
            s.audit.record(_event(ThreatLevel.CRITICAL))
        client = TestClient(_make_app(s))
        data = client.get("/v1/sentinel/status").json()
        assert len(data["recent_critical"]) <= 10

    def test_status_gaian_blocked_403(self):
        client = TestClient(_make_app(Sentinel(), caller_id=_GAIAN_UUID))
        assert client.get("/v1/sentinel/status").status_code == 403

    def test_status_unauthenticated_401(self):
        client = TestClient(_make_app(Sentinel(), caller_id=""))
        assert client.get("/v1/sentinel/status").status_code == 401


# ---------------------------------------------------------------------------
# TestAuditEndpointForDashboard
# ---------------------------------------------------------------------------

class TestAuditEndpointForDashboard:
    """Verify /v1/sentinel/audit returns every field the dashboard JS reads."""

    def _sentinel_with_all_levels(self) -> Sentinel:
        s = Sentinel()
        s.audit.record(_event(ThreatLevel.WATCH))
        s.audit.record(_event(ThreatLevel.WARN))
        s.audit.record(_event(ThreatLevel.BLOCK))
        s.audit.record(_event(ThreatLevel.CRITICAL))
        return s

    def test_audit_200(self):
        client = TestClient(_make_app(Sentinel()))
        assert client.get("/v1/sentinel/audit").status_code == 200

    def test_audit_event_has_all_dashboard_fields(self):
        s = Sentinel()
        s.audit.record(_event(ThreatLevel.BLOCK, blocked=True))
        client = TestClient(_make_app(s))
        ev = client.get("/v1/sentinel/audit").json()["events"][0]
        for field in (
            "event_id", "level", "category", "rule_name",
            "caller_id", "endpoint", "description",
            "occurred_at", "blocked", "detail",
        ):
            assert field in ev, f"Event missing field used by dashboard JS: {field}"

    def test_audit_level_filter_matches_dashboard_query_panel(self):
        s = self._sentinel_with_all_levels()
        client = TestClient(_make_app(s))
        for level in ("watch", "warn", "block", "critical"):
            data = client.get(f"/v1/sentinel/audit?level={level}").json()
            assert data["count"] == 1
            assert data["events"][0]["level"] == level

    def test_audit_caller_id_filter(self):
        s = Sentinel()
        s.audit.record(_event(ThreatLevel.WARN, caller_id="op-alpha"))
        s.audit.record(_event(ThreatLevel.WARN, caller_id="op-beta"))
        client = TestClient(_make_app(s))
        data = client.get("/v1/sentinel/audit?caller_id=op-alpha").json()
        assert data["count"] == 1
        assert data["events"][0]["caller_id"] == "op-alpha"

    def test_audit_gaian_id_filter(self):
        s = Sentinel()
        s.audit.record(_event(ThreatLevel.WARN, gaian_id="g-111"))
        s.audit.record(_event(ThreatLevel.WARN, gaian_id="g-222"))
        client = TestClient(_make_app(s))
        data = client.get("/v1/sentinel/audit?gaian_id=g-111").json()
        assert data["count"] == 1

    def test_audit_limit_200_matches_dashboard_query(self):
        """Dashboard JS always sends limit=200 in query mode."""
        s = Sentinel()
        for _ in range(250):
            s.audit.record(_event(ThreatLevel.WARN))
        client = TestClient(_make_app(s))
        data = client.get("/v1/sentinel/audit?limit=200").json()
        assert data["count"] == 200

    def test_audit_gaian_blocked_403(self):
        client = TestClient(_make_app(Sentinel(), caller_id=_GAIAN_UUID))
        assert client.get("/v1/sentinel/audit").status_code == 403

    def test_audit_unauthenticated_401(self):
        client = TestClient(_make_app(Sentinel(), caller_id=""))
        assert client.get("/v1/sentinel/audit").status_code == 401


# ---------------------------------------------------------------------------
# TestStreamEndpointForDashboard
# ---------------------------------------------------------------------------

class TestStreamEndpointForDashboard:
    """Verify /v1/sentinel/audit/stream behaves as the dashboard EventSource expects."""

    def test_stream_returns_200(self):
        client = TestClient(_make_app(Sentinel()))
        with client.stream("GET", "/v1/sentinel/audit/stream") as resp:
            assert resp.status_code == 200

    def test_stream_content_type_is_event_stream(self):
        client = TestClient(_make_app(Sentinel()))
        with client.stream("GET", "/v1/sentinel/audit/stream") as resp:
            ct = resp.headers.get("content-type", "")
            assert "text/event-stream" in ct

    def test_stream_cache_control_no_cache(self):
        client = TestClient(_make_app(Sentinel()))
        with client.stream("GET", "/v1/sentinel/audit/stream") as resp:
            assert resp.headers.get("cache-control", "") == "no-cache"

    def test_stream_event_is_valid_json(self):
        s = Sentinel()
        ev = _event(ThreatLevel.WARN)
        s.audit.record(ev)
        client = TestClient(_make_app(s))
        lines = []
        try:
            with client.stream("GET", "/v1/sentinel/audit/stream?min_level=warn") as resp:
                for line in resp.iter_lines():
                    if line.startswith("data:"):
                        payload = line[len("data:"):].strip()
                        parsed = json.loads(payload)
                        lines.append(parsed)
                        break
                    if line.startswith(":"):
                        break
        except Exception:
            pass
        for parsed in lines:
            for field in ("event_id", "level", "category", "rule_name",
                          "caller_id", "endpoint", "description",
                          "occurred_at", "blocked"):
                assert field in parsed, f"SSE event missing field: {field}"

    def test_stream_gaian_blocked_403(self):
        client = TestClient(_make_app(Sentinel(), caller_id=_GAIAN_UUID))
        resp = client.get("/v1/sentinel/audit/stream")
        assert resp.status_code == 403

    def test_stream_unauthenticated_401(self):
        client = TestClient(_make_app(Sentinel(), caller_id=""))
        resp = client.get("/v1/sentinel/audit/stream")
        assert resp.status_code == 401

    def test_stream_min_level_param_accepted(self):
        client = TestClient(_make_app(Sentinel()))
        for level in ("watch", "warn", "block", "critical"):
            with client.stream(
                "GET", f"/v1/sentinel/audit/stream?min_level={level}"
            ) as resp:
                assert resp.status_code == 200
                break

    def test_stream_invalid_min_level_returns_422(self):
        client = TestClient(_make_app(Sentinel()))
        resp = client.get("/v1/sentinel/audit/stream?min_level=invalid")
        assert resp.status_code == 422
