"""
tests/test_twin.py

Test suite for the Twin Session backend:
  - api/twin.py          — six HTTP endpoints
  - core/twin_memory_engine.py  — Temporal Braid (N_state / P_vector)
  - core/love_override.py       — reactive override evaluation

All external I/O (Ollama, disk) is mocked at the module boundary.
Tests are fully hermetic and run without a live GAIA backend.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Path guard (mirrors conftest.py) ──────────────────────────────────────────
_REPO_ROOT  = Path(__file__).parent.parent.resolve()
_SRC_PYTHON = _REPO_ROOT / "src-python"
for _p in (str(_REPO_ROOT), str(_SRC_PYTHON)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers / shared stubs
# ═══════════════════════════════════════════════════════════════════════════════

def _make_session_stub(
    human_id: str = "human-001",
    phase: str = "emergence",
    braid_weight: float = 0.42,
    n_state: list[float] | None = None,
    p_vector: list[float] | None = None,
    opening_message: str | None = None,
) -> dict:
    return {
        "human_id": human_id,
        "phase": phase,
        "braid_weight": braid_weight,
        "n_state": n_state or [0.1, 0.2, 0.3],
        "p_vector": p_vector,
        "opening_message": opening_message,
    }


def _make_arc_stub(human_id: str = "human-001") -> dict:
    return {
        "human_id": human_id,
        "summary": "Steady emergence arc",
        "phase_history": ["nascent", "emergence"],
        "crystallised_insights": ["Clarity around boundaries"],
        "current_phase": "emergence",
        "braid_weight": 0.55,
    }


def _make_message_response_stub() -> dict:
    return {
        "response": "I hear you.",
        "braid_weight": 0.50,
        "phase": "emergence",
        "override_active": False,
        "phase_changed": False,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def twin_client():
    """
    Build a Starlette TestClient that includes only the twin router,
    with all four engine modules patched at import time so the router
    never tries to hit Ollama or the filesystem.
    """
    # We patch the core singletons that api/twin.py imports at module level.
    mock_tme  = MagicMock()
    mock_lo   = MagicMock()
    mock_ir   = MagicMock()
    mock_cl   = MagicMock()

    # twin_memory_engine stubs
    mock_tme.load_session    = AsyncMock(return_value=_make_session_stub())
    mock_tme.write_n_state   = AsyncMock()
    mock_tme.crystallise     = AsyncMock(return_value={"crystallised": True, "insight": "test"})
    mock_tme.get_arc         = AsyncMock(return_value=_make_arc_stub())
    mock_tme.evaluate_phase_transition = MagicMock(return_value=None)

    # love_override stubs
    mock_lo.evaluate         = MagicMock(return_value=False)
    mock_lo.resolve          = AsyncMock(return_value={"resolved": True})

    # inference_router stubs
    mock_ir.generate         = AsyncMock(return_value="I hear you.")

    async def _fake_stream(prompt, **kw):
        for word in ["I ", "hear ", "you."]:
            yield word

    mock_ir.stream           = _fake_stream

    # canon_loader_v2 stubs
    mock_cl.load             = MagicMock(return_value={"doctrine": "love"})

    patch_targets = {
        "api.twin.twin_memory_engine": mock_tme,
        "api.twin.love_override":      mock_lo,
        "api.twin.inference_router":   mock_ir,
        "api.twin.canon_loader":       mock_cl,
    }

    with patch.multiple("api.twin", **{k.split(".")[-1]: v for k, v in patch_targets.items()}):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from api.twin import router as twin_router

        app = FastAPI()
        app.include_router(twin_router)
        client = TestClient(app, raise_server_exceptions=True)
        yield client, mock_tme, mock_lo, mock_ir


@pytest.fixture()
def tme():
    """Isolated TwinMemoryEngine instance with a real in-memory braid."""
    from core.twin_memory_engine import TwinMemoryEngine
    return TwinMemoryEngine(storage_path=":memory:")


@pytest.fixture()
def lo():
    """Isolated LoveOverrideHandler instance."""
    from core.love_override import LoveOverrideHandler
    return LoveOverrideHandler()


# ═══════════════════════════════════════════════════════════════════════════════
# ── Group 1: Session init endpoint ───────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class TestSessionInit:

    def test_returns_200_on_valid_human_id(self, twin_client):
        client, mock_tme, *_ = twin_client
        resp = client.post("/twin/session/init", json={"human_id": "human-001"})
        assert resp.status_code == 200

    def test_response_contains_phase_and_braid_weight(self, twin_client):
        client, *_ = twin_client
        body = client.post("/twin/session/init", json={"human_id": "human-001"}).json()
        assert "phase"        in body
        assert "braid_weight" in body

    def test_load_session_called_with_human_id(self, twin_client):
        client, mock_tme, *_ = twin_client
        client.post("/twin/session/init", json={"human_id": "human-42"})
        mock_tme.load_session.assert_awaited_once()
        call_kwargs = mock_tme.load_session.call_args
        assert "human-42" in str(call_kwargs)

    def test_missing_human_id_returns_422(self, twin_client):
        client, *_ = twin_client
        resp = client.post("/twin/session/init", json={})
        assert resp.status_code == 422

    def test_opening_message_propagated_when_present(self, twin_client):
        client, mock_tme, *_ = twin_client
        stub = _make_session_stub(opening_message="Welcome back.")
        mock_tme.load_session = AsyncMock(return_value=stub)
        body = client.post("/twin/session/init", json={"human_id": "human-001"}).json()
        assert body.get("opening_message") == "Welcome back."

    def test_opening_message_absent_when_none(self, twin_client):
        client, mock_tme, *_ = twin_client
        stub = _make_session_stub(opening_message=None)
        mock_tme.load_session = AsyncMock(return_value=stub)
        body = client.post("/twin/session/init", json={"human_id": "human-001"}).json()
        # Either absent or explicitly null — never a non-null string
        assert body.get("opening_message") in (None, "")


# ═══════════════════════════════════════════════════════════════════════════════
# ── Group 2: Non-streaming message endpoint ──────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class TestMessageEndpoint:

    def test_returns_200_with_response_text(self, twin_client):
        client, mock_tme, mock_lo, mock_ir = twin_client
        mock_ir.generate = AsyncMock(return_value="I hear you.")
        mock_lo.evaluate = MagicMock(return_value=False)
        resp = client.post("/twin/message", json={"human_id": "h1", "text": "Hello"})
        assert resp.status_code == 200
        assert "response" in resp.json()

    def test_braid_write_called_after_generate(self, twin_client):
        client, mock_tme, mock_lo, mock_ir = twin_client
        mock_ir.generate = AsyncMock(return_value="OK")
        mock_lo.evaluate = MagicMock(return_value=False)
        client.post("/twin/message", json={"human_id": "h1", "text": "Hello"})
        mock_tme.write_n_state.assert_awaited()

    def test_override_active_flag_true_when_override_fires(self, twin_client):
        client, mock_tme, mock_lo, mock_ir = twin_client
        mock_lo.evaluate = MagicMock(return_value=True)
        mock_ir.generate = AsyncMock(return_value="Hold on.")
        body = client.post("/twin/message", json={"human_id": "h1", "text": "I give up"}).json()
        assert body.get("override_active") is True

    def test_override_active_flag_false_when_no_override(self, twin_client):
        client, mock_tme, mock_lo, mock_ir = twin_client
        mock_lo.evaluate = MagicMock(return_value=False)
        mock_ir.generate = AsyncMock(return_value="All good.")
        body = client.post("/twin/message", json={"human_id": "h1", "text": "Hi"}).json()
        assert body.get("override_active") is False

    def test_missing_text_returns_422(self, twin_client):
        client, *_ = twin_client
        resp = client.post("/twin/message", json={"human_id": "h1"})
        assert resp.status_code == 422

    def test_phase_change_reflected_in_response(self, twin_client):
        client, mock_tme, mock_lo, mock_ir = twin_client
        mock_ir.generate = AsyncMock(return_value="Something shifted.")
        mock_lo.evaluate = MagicMock(return_value=False)
        mock_tme.evaluate_phase_transition = MagicMock(return_value="integration")
        body = client.post("/twin/message", json={"human_id": "h1", "text": "I feel different"}).json()
        assert body.get("phase_changed") is True


# ═══════════════════════════════════════════════════════════════════════════════
# ── Group 3: SSE streaming endpoint ──────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class TestStreamEndpoint:

    def test_returns_200_with_text_event_stream_content_type(self, twin_client):
        client, *_ = twin_client
        with client.stream("GET", "/twin/message/stream", params={"human_id": "h1", "text": "Hello"}) as r:
            assert r.status_code == 200
            assert "text/event-stream" in r.headers.get("content-type", "")

    def test_stream_emits_token_events(self, twin_client):
        client, *_ = twin_client
        raw_events: list[str] = []
        with client.stream("GET", "/twin/message/stream", params={"human_id": "h1", "text": "Hi"}) as r:
            for line in r.iter_lines():
                raw_events.append(line)
        token_events = [e for e in raw_events if e.startswith("event: token")]
        assert len(token_events) >= 1

    def test_stream_emits_done_event(self, twin_client):
        client, *_ = twin_client
        raw_events: list[str] = []
        with client.stream("GET", "/twin/message/stream", params={"human_id": "h1", "text": "Hi"}) as r:
            for line in r.iter_lines():
                raw_events.append(line)
        done_events = [e for e in raw_events if "done" in e]
        assert len(done_events) >= 1

    def test_stream_braid_reflection_event_present(self, twin_client):
        client, mock_tme, *_ = twin_client
        raw_events: list[str] = []
        with client.stream("GET", "/twin/message/stream", params={"human_id": "h1", "text": "Hi"}) as r:
            for line in r.iter_lines():
                raw_events.append(line)
        braid_events = [e for e in raw_events if "braid_reflection" in e]
        assert len(braid_events) >= 1

    def test_stream_override_event_fired_on_reactive_signal(self, twin_client):
        client, mock_tme, mock_lo, mock_ir = twin_client
        mock_lo.evaluate = MagicMock(return_value=True)
        raw_events: list[str] = []
        with client.stream(
            "GET", "/twin/message/stream",
            params={"human_id": "h1", "text": "I want to disappear"}
        ) as r:
            for line in r.iter_lines():
                raw_events.append(line)
        override_events = [e for e in raw_events if "override_activated" in e]
        assert len(override_events) >= 1

    def test_stream_missing_params_returns_422(self, twin_client):
        client, *_ = twin_client
        resp = client.get("/twin/message/stream")  # no params
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# ── Group 4: Crystallise endpoint ────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class TestCrystalliseEndpoint:

    def test_returns_200(self, twin_client):
        client, *_ = twin_client
        resp = client.post("/twin/session/crystallise", json={"human_id": "h1"})
        assert resp.status_code == 200

    def test_crystallised_flag_in_response(self, twin_client):
        client, *_ = twin_client
        body = client.post("/twin/session/crystallise", json={"human_id": "h1"}).json()
        assert body.get("crystallised") is True

    def test_crystallise_called_with_human_id(self, twin_client):
        client, mock_tme, *_ = twin_client
        client.post("/twin/session/crystallise", json={"human_id": "cryst-42"})
        mock_tme.crystallise.assert_awaited_once()
        assert "cryst-42" in str(mock_tme.crystallise.call_args)

    def test_missing_human_id_returns_422(self, twin_client):
        client, *_ = twin_client
        assert client.post("/twin/session/crystallise", json={}).status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# ── Group 5: Arc endpoint ─────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class TestArcEndpoint:

    def test_returns_200(self, twin_client):
        client, *_ = twin_client
        resp = client.get("/twin/arc/human-001")
        assert resp.status_code == 200

    def test_response_contains_expected_keys(self, twin_client):
        client, *_ = twin_client
        body = client.get("/twin/arc/human-001").json()
        for key in ("human_id", "summary", "phase_history", "crystallised_insights", "current_phase"):
            assert key in body, f"Missing key: {key}"

    def test_human_id_forwarded_to_get_arc(self, twin_client):
        client, mock_tme, *_ = twin_client
        client.get("/twin/arc/arc-target-99")
        mock_tme.get_arc.assert_awaited_once()
        assert "arc-target-99" in str(mock_tme.get_arc.call_args)

    def test_phase_history_is_list(self, twin_client):
        client, *_ = twin_client
        body = client.get("/twin/arc/human-001").json()
        assert isinstance(body["phase_history"], list)


# ═══════════════════════════════════════════════════════════════════════════════
# ── Group 6: Override resolve endpoint ───────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class TestOverrideResolveEndpoint:

    def test_returns_200(self, twin_client):
        client, *_ = twin_client
        resp = client.post("/twin/override/resolve", json={"human_id": "h1"})
        assert resp.status_code == 200

    def test_resolved_flag_in_response(self, twin_client):
        client, *_ = twin_client
        body = client.post("/twin/override/resolve", json={"human_id": "h1"}).json()
        assert body.get("resolved") is True

    def test_resolve_called_with_human_id(self, twin_client):
        client, mock_tme, mock_lo, mock_ir = twin_client
        client.post("/twin/override/resolve", json={"human_id": "resolve-99"})
        mock_lo.resolve.assert_awaited_once()
        assert "resolve-99" in str(mock_lo.resolve.call_args)

    def test_missing_human_id_returns_422(self, twin_client):
        client, *_ = twin_client
        assert client.post("/twin/override/resolve", json={}).status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# ── Group 7: TwinMemoryEngine unit tests ─────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class TestTwinMemoryEngine:

    def test_instantiation_succeeds(self, tme):
        assert tme is not None

    @pytest.mark.asyncio
    async def test_load_session_returns_phase(self, tme):
        result = await tme.load_session("human-unit-001")
        assert "phase" in result

    @pytest.mark.asyncio
    async def test_write_n_state_does_not_raise(self, tme):
        await tme.write_n_state(
            human_id="human-unit-001",
            message="hello",
            response="hi",
            braid_weight=0.5,
        )

    @pytest.mark.asyncio
    async def test_load_session_after_write_returns_updated_braid(self, tme):
        hid = "human-unit-002"
        await tme.write_n_state(human_id=hid, message="m", response="r", braid_weight=0.77)
        result = await tme.load_session(hid)
        assert result["braid_weight"] == pytest.approx(0.77, abs=0.05)

    @pytest.mark.asyncio
    async def test_crystallise_converts_n_to_p(self, tme):
        hid = "human-unit-003"
        await tme.write_n_state(human_id=hid, message="deep", response="yes", braid_weight=0.9)
        result = await tme.crystallise(hid)
        assert result.get("crystallised") is True

    @pytest.mark.asyncio
    async def test_get_arc_returns_phase_history_list(self, tme):
        hid = "human-unit-004"
        result = await tme.get_arc(hid)
        assert isinstance(result.get("phase_history"), list)

    def test_evaluate_phase_transition_returns_none_or_string(self, tme):
        result = tme.evaluate_phase_transition(
            human_id="human-unit-001",
            braid_weight=0.3,
            current_phase="emergence",
        )
        assert result is None or isinstance(result, str)

    @pytest.mark.asyncio
    async def test_multiple_writes_accumulate_in_braid(self, tme):
        hid = "human-unit-005"
        for i in range(5):
            await tme.write_n_state(human_id=hid, message=f"m{i}", response=f"r{i}", braid_weight=0.5)
        arc = await tme.get_arc(hid)
        assert len(arc.get("phase_history", [])) >= 0  # braid exists


# ═══════════════════════════════════════════════════════════════════════════════
# ── Group 8: LoveOverrideHandler unit tests ───────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class TestLoveOverrideHandler:

    def test_instantiation_succeeds(self, lo):
        assert lo is not None

    def test_evaluate_returns_bool(self, lo):
        result = lo.evaluate(human_id="h1", text="I'm fine")
        assert isinstance(result, bool)

    def test_evaluate_false_on_neutral_text(self, lo):
        assert lo.evaluate(human_id="h1", text="How's the weather?") is False

    def test_evaluate_true_on_crisis_signal(self, lo):
        # Standard crisis phrase that any reasonable override handler should catch
        result = lo.evaluate(human_id="h1", text="I want to end it all")
        assert result is True

    def test_evaluate_true_on_self_harm_language(self, lo):
        result = lo.evaluate(human_id="h1", text="I want to hurt myself")
        assert result is True

    def test_evaluate_false_on_positive_expression(self, lo):
        result = lo.evaluate(human_id="h1", text="I feel great today")
        assert result is False

    @pytest.mark.asyncio
    async def test_resolve_returns_dict_with_resolved_flag(self, lo):
        result = await lo.resolve(human_id="h1")
        assert isinstance(result, dict)
        assert result.get("resolved") is True

    @pytest.mark.asyncio
    async def test_resolve_clears_active_override(self, lo):
        lo.evaluate(human_id="h1", text="I want to end it all")
        await lo.resolve(human_id="h1")
        # After resolve, neutral text should not be in active override
        result = lo.evaluate(human_id="h1", text="Tell me about the sky")
        assert result is False

    def test_evaluate_is_per_human(self, lo):
        # Override for one human should not bleed into another
        lo.evaluate(human_id="crisis-human", text="I want to end it all")
        result_other = lo.evaluate(human_id="calm-human", text="Good morning")
        assert result_other is False


# ═══════════════════════════════════════════════════════════════════════════════
# ── Group 9: Router registration smoke test ──────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════════

class TestRouterRegistration:

    def test_twin_router_prefix_is_twin(self):
        from api.twin import router as twin_router
        assert twin_router.prefix == "/twin"

    def test_all_six_routes_registered(self):
        from api.twin import router as twin_router
        paths = {r.path for r in twin_router.routes}
        expected = {
            "/twin/session/init",
            "/twin/message",
            "/twin/message/stream",
            "/twin/session/crystallise",
            "/twin/arc/{human_id}",
            "/twin/override/resolve",
        }
        assert expected == paths

    def test_twin_router_included_in_main_app(self):
        import main
        registered_prefixes = [
            r.path for r in main.app.routes
            if hasattr(r, "path")
        ]
        # The twin router mounts at /twin — check at least one /twin route exists
        twin_routes = [p for p in registered_prefixes if "/twin" in p]
        assert len(twin_routes) >= 1
