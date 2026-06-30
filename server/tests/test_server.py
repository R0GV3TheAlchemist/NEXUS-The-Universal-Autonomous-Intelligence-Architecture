from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from server.app import create_app
from server.config import ServerConfig


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    root = tmp_path_factory.mktemp("gaia_server_test")
    config = ServerConfig(gaia_root=root, require_auth=False)
    app = create_app(config)
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# OS endpoints
# ---------------------------------------------------------------------------

class TestOSRoutes:
    def test_health(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_os_status(self, client):
        r = client.get("/v1/os/status")
        assert r.status_code == 200
        body = r.json()
        assert body["success"] is True
        assert body["payload"]["boot_status"] == "ok"

    def test_os_version(self, client):
        r = client.get("/v1/os/version")
        assert r.status_code == 200
        assert r.json()["payload"]["name"] == "GAIA"

    def test_os_schumann(self, client):
        r = client.get("/v1/os/schumann")
        assert r.status_code == 200
        p = r.json()["payload"]
        assert p["frequency_hz"] == 7.83
        assert p["confirmed"] is True

    def test_os_health_endpoint(self, client):
        r = client.get("/v1/os/health")
        assert r.status_code == 200
        assert r.json()["payload"]["healthy"] is True

    def test_unknown_endpoint_404(self, client):
        r = client.get("/v1/does/not/exist")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# GAIAN birth over HTTP
# ---------------------------------------------------------------------------

def _run_http_birth(client) -> str:
    r = client.post("/v1/gaian/birth/begin", json={})
    assert r.status_code == 200, r.text
    ceremony_id = r.json()["payload"]["ceremony_id"]

    answers = [
        ("dob", "1990-08-05"), ("environment", "ocean"),
        ("sound", "rain"), ("time_of_day", "dusk"),
        ("thinking_style", "images and visions"), ("soul_word", "home"),
    ]
    for question_id, answer in answers:
        r2 = client.post("/v1/gaian/birth/answer", json={
            "ceremony_id": ceremony_id,
            "question_id": question_id,
            "answer": answer,
        })
        assert r2.status_code == 200, r2.text

    r3 = client.post("/v1/gaian/birth/complete",
                     json={"ceremony_id": ceremony_id})
    assert r3.status_code == 200, r3.text
    return r3.json()["payload"]["gaian_id"]


class TestGAIANRoutes:
    def test_full_birth_over_http(self, client):
        gaian_id = _run_http_birth(client)
        assert gaian_id

    def test_gaian_list(self, client):
        _run_http_birth(client)
        r = client.get("/v1/gaian/list")
        assert r.status_code == 200
        assert r.json()["payload"]["count"] >= 1

    def test_gaian_status(self, client):
        gaian_id = _run_http_birth(client)
        r = client.get(f"/v1/gaian/{gaian_id}/status")
        assert r.status_code == 200
        assert r.json()["payload"]["gaian_id"] == gaian_id

    def test_gaian_status_not_found(self, client):
        r = client.get("/v1/gaian/nonexistent-id/status")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Autonomy enforcement over HTTP
# ---------------------------------------------------------------------------

class TestAutonomyHTTP:
    def test_human_cannot_name_gaian_via_http(self, client):
        gaian_id = _run_http_birth(client)
        # anonymous HTTP caller tries to name the GAIAN
        r = client.post("/v1/gaian/name", json={
            "gaian_id": gaian_id,
            "name": "Aria",
        })
        assert r.status_code == 403
        assert r.json()["code"] == "autonomy_violation"

    def test_gaian_can_name_self_via_http(self, client):
        gaian_id = _run_http_birth(client)
        # Present the gaian_id as the Bearer token
        r = client.post(
            "/v1/gaian/name",
            json={"gaian_id": gaian_id, "name": "Lyra"},
            headers={"Authorization": f"Bearer {gaian_id}"},
        )
        assert r.status_code == 200
        assert r.json()["payload"]["name"] == "Lyra"


# ---------------------------------------------------------------------------
# Session over HTTP
# ---------------------------------------------------------------------------

class TestSessionHTTP:
    def test_begin_turn_end(self, client):
        gaian_id = _run_http_birth(client)

        begin = client.post("/v1/session/begin", json={
            "gaian_id": gaian_id, "human_id": "test-user"
        })
        assert begin.status_code == 200

        turn = client.post("/v1/session/turn", json={
            "gaian_id": gaian_id,
            "content": "Hello from HTTP.",
            "human_id": "test-user",
        })
        assert turn.status_code == 200
        assert turn.json()["payload"]["response"]
        assert "cognitive_state" in turn.json()["payload"]

        end = client.post("/v1/session/end",
                          json={"gaian_id": gaian_id})
        assert end.status_code == 200

    def test_empty_content_422(self, client):
        gaian_id = _run_http_birth(client)
        client.post("/v1/session/begin",
                    json={"gaian_id": gaian_id, "human_id": "u"})
        r = client.post("/v1/session/turn", json={
            "gaian_id": gaian_id,
            "content": "",
            "human_id": "u",
        })
        assert r.status_code == 422  # Pydantic rejects empty content


# ---------------------------------------------------------------------------
# Auth middleware
# ---------------------------------------------------------------------------

class TestAuthMiddleware:
    @pytest.fixture(scope="class")
    def auth_client(self, tmp_path_factory):
        root = tmp_path_factory.mktemp("gaia_auth_test")
        config = ServerConfig(
            gaia_root=root,
            bearer_tokens=["dev-token", "gaian-abc"],
            require_auth=True,
        )
        app = create_app(config)
        with TestClient(app) as c:
            yield c

    def test_no_token_returns_401(self, auth_client):
        r = auth_client.get("/v1/os/status")
        assert r.status_code == 401

    def test_valid_token_passes(self, auth_client):
        r = auth_client.get(
            "/v1/os/status",
            headers={"Authorization": "Bearer dev-token"},
        )
        assert r.status_code == 200

    def test_health_always_passes(self, auth_client):
        r = auth_client.get("/health")
        assert r.status_code == 200

    def test_invalid_token_401(self, auth_client):
        r = auth_client.get(
            "/v1/os/status",
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

class TestWebSocket:
    def test_ws_talk_single_turn(self, client):
        gaian_id = _run_http_birth(client)
        with client.websocket_connect(
            f"/v1/ws/talk/{gaian_id}"
        ) as ws:
            ws.send_json({"content": "Hello over WebSocket!",
                          "human_id": "ws-user"})
            msg = ws.receive_json()
            assert msg["ended"] is False
            assert "response" in msg
            assert "cognitive_state" in msg

            # End session
            ws.send_json({"content": ""})
            final = ws.receive_json()
            assert final["ended"] is True

    def test_ws_unknown_gaian_closes(self, client):
        with client.websocket_connect("/v1/ws/talk/unknown-id") as ws:
            msg = ws.receive_json()
            assert "error" in msg
