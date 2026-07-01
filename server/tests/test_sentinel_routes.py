"""
Tests for /v1/sentinel/status and /v1/sentinel/audit routes.

Uses FastAPI TestClient (synchronous httpx) so no async test runner
needed. The Sentinel singleton is injected directly onto the router
to avoid booting the full OS.
"""
from __future__ import annotations

import json
import pytest
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from core.sentinel.sentinel import Sentinel
from core.sentinel.threat import ThreatLevel, ThreatCategory, ThreatEvent
from server.routes_sentinel import router as sentinel_router


# ---------------------------------------------------------------------------
# App fixture
# ---------------------------------------------------------------------------

def _make_app(sentinel: Sentinel, caller_id: str = "operator-1") -> FastAPI:
    """
    Minimal FastAPI app with the Sentinel router mounted.
    Injects a fake request.state.caller_id so the operator
    auth dependency is satisfied without a real Bearer token.
    """
    from fastapi import FastAPI, Request
    from fastapi.middleware.base import BaseHTTPMiddleware

    app = FastAPI()

    class FakeAuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            request.state.caller_id = caller_id
            return await call_next(request)

    app.add_middleware(FakeAuthMiddleware)
    sentinel_router.sentinel = sentinel
    app.include_router(sentinel_router)
    return app


def _event(
    level=ThreatLevel.WARN,
    caller_id="c1",
    gaian_id=None,
    category=ThreatCategory.RATE_LIMIT,
    occurred_at=None,
) -> ThreatEvent:
    return ThreatEvent(
        level=level,
        category=category,
        rule_name="test_rule",
        caller_id=caller_id,
        endpoint="/v1/os/status",
        gaian_id=gaian_id,
        description="test event",
        occurred_at=occurred_at or datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# /v1/sentinel/status
# ---------------------------------------------------------------------------

class TestSentinelStatus:
    def test_status_returns_200(self):
        s = Sentinel()
        client = TestClient(_make_app(s))
        resp = client.get("/v1/sentinel/status")
        assert resp.status_code == 200

    def test_status_contains_rules(self):
        s = Sentinel()
        client = TestClient(_make_app(s))
        data = client.get("/v1/sentinel/status").json()
        assert "active_rules" in data
        assert len(data["active_rules"]) == 7  # 7 built-in rules
        assert data["rule_count"] == 7

    def test_status_contains_audit_stats(self):
        s = Sentinel()
        client = TestClient(_make_app(s))
        data = client.get("/v1/sentinel/status").json()
        assert "audit_stats" in data
        assert all(k in data["audit_stats"]
                   for k in ("total", "watch", "warn", "block", "critical"))

    def test_status_recent_blocked_populated(self):
        s = Sentinel()
        s.audit.record(_event(ThreatLevel.BLOCK))
        s.audit.record(_event(ThreatLevel.BLOCK))
        client = TestClient(_make_app(s))
        data = client.get("/v1/sentinel/status").json()
        assert len(data["recent_blocked"]) == 2

    def test_status_recent_critical_populated(self):
        s = Sentinel()
        s.audit.record(_event(ThreatLevel.CRITICAL))
        client = TestClient(_make_app(s))
        data = client.get("/v1/sentinel/status").json()
        assert len(data["recent_critical"]) == 1

    def test_status_blocked_for_gaian_caller(self):
        s = Sentinel()
        # GAIAN IDs are UUIDs
        gaian_id = "550e8400-e29b-41d4-a716-446655440000"
        client = TestClient(_make_app(s, caller_id=gaian_id))
        resp = client.get("/v1/sentinel/status")
        assert resp.status_code == 403

    def test_status_blocked_for_unauthenticated(self):
        s = Sentinel()
        client = TestClient(_make_app(s, caller_id=""))
        resp = client.get("/v1/sentinel/status")
        assert resp.status_code == 401

    def test_status_503_when_sentinel_not_set(self):
        from fastapi import FastAPI, Request
        from fastapi.middleware.base import BaseHTTPMiddleware
        from server.routes_sentinel import router as r
        import importlib
        import server.routes_sentinel as sr_module
        # Temporarily remove sentinel from router
        old = getattr(r, "sentinel", None)
        if hasattr(r, "sentinel"):
            delattr(r, "sentinel")
        app = FastAPI()
        class FM(BaseHTTPMiddleware):
            async def dispatch(self, request, call_next):
                request.state.caller_id = "operator-1"
                return await call_next(request)
        app.add_middleware(FM)
        app.include_router(r)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/v1/sentinel/status")
        assert resp.status_code == 503
        # Restore
        if old is not None:
            r.sentinel = old


# ---------------------------------------------------------------------------
# /v1/sentinel/audit
# ---------------------------------------------------------------------------

class TestSentinelAudit:
    def _populated(self) -> Sentinel:
        s = Sentinel()
        s.audit.record(_event(ThreatLevel.WATCH,  caller_id="a"))
        s.audit.record(_event(ThreatLevel.WARN,   caller_id="b"))
        s.audit.record(_event(ThreatLevel.BLOCK,  caller_id="c"))
        s.audit.record(_event(ThreatLevel.CRITICAL, caller_id="d"))
        return s

    def test_audit_returns_all_events(self):
        s = self._populated()
        client = TestClient(_make_app(s))
        data = client.get("/v1/sentinel/audit").json()
        assert data["count"] == 4

    def test_filter_by_exact_level(self):
        s = self._populated()
        client = TestClient(_make_app(s))
        data = client.get("/v1/sentinel/audit?level=warn").json()
        assert data["count"] == 1
        assert data["events"][0]["level"] == "warn"

    def test_filter_by_min_level(self):
        s = self._populated()
        client = TestClient(_make_app(s))
        data = client.get("/v1/sentinel/audit?min_level=block").json()
        assert data["count"] == 2  # block + critical
        levels = {e["level"] for e in data["events"]}
        assert levels == {"block", "critical"}

    def test_filter_by_caller_id(self):
        s = self._populated()
        client = TestClient(_make_app(s))
        data = client.get("/v1/sentinel/audit?caller_id=c").json()
        assert data["count"] == 1
        assert data["events"][0]["caller_id"] == "c"

    def test_filter_by_gaian_id(self):
        s = Sentinel()
        s.audit.record(_event(ThreatLevel.WARN, gaian_id="g1"))
        s.audit.record(_event(ThreatLevel.WARN, gaian_id="g2"))
        client = TestClient(_make_app(s))
        data = client.get("/v1/sentinel/audit?gaian_id=g1").json()
        assert data["count"] == 1
        assert data["events"][0]["gaian_id"] == "g1"

    def test_filter_by_since(self):
        s = Sentinel()
        old_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
        new_time = datetime.now(timezone.utc)
        s.audit.record(_event(ThreatLevel.WARN, occurred_at=old_time))
        s.audit.record(_event(ThreatLevel.WARN, occurred_at=new_time))
        client = TestClient(_make_app(s))
        since = "2025-01-01T00:00:00Z"
        data  = client.get(f"/v1/sentinel/audit?since={since}").json()
        assert data["count"] == 1

    def test_limit_respected(self):
        s = Sentinel()
        for _ in range(20):
            s.audit.record(_event(ThreatLevel.WARN))
        client = TestClient(_make_app(s))
        data = client.get("/v1/sentinel/audit?limit=5").json()
        assert data["count"] == 5

    def test_invalid_level_returns_422(self):
        s = Sentinel()
        client = TestClient(_make_app(s))
        resp = client.get("/v1/sentinel/audit?level=nonexistent")
        assert resp.status_code == 422

    def test_invalid_since_returns_422(self):
        s = Sentinel()
        client = TestClient(_make_app(s))
        resp = client.get("/v1/sentinel/audit?since=not-a-date")
        assert resp.status_code == 422

    def test_events_most_recent_first(self):
        s = Sentinel()
        t1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        t2 = datetime(2026, 6, 1, tzinfo=timezone.utc)
        s.audit.record(_event(ThreatLevel.WARN, occurred_at=t1))
        s.audit.record(_event(ThreatLevel.WARN, occurred_at=t2))
        client = TestClient(_make_app(s))
        data   = client.get("/v1/sentinel/audit").json()
        times  = [e["occurred_at"] for e in data["events"]]
        assert times[0] > times[1]  # most recent first

    def test_gaian_caller_denied(self):
        s = Sentinel()
        gaian_id = "550e8400-e29b-41d4-a716-446655440000"
        client = TestClient(_make_app(s, caller_id=gaian_id))
        resp = client.get("/v1/sentinel/audit")
        assert resp.status_code == 403

    def test_event_schema_fields_present(self):
        s = Sentinel()
        s.audit.record(_event(ThreatLevel.BLOCK))
        client = TestClient(_make_app(s))
        data = client.get("/v1/sentinel/audit").json()
        e = data["events"][0]
        for field in ("event_id", "level", "category", "rule_name",
                      "caller_id", "endpoint", "description",
                      "occurred_at", "blocked"):
            assert field in e, f"Missing field: {field}"
