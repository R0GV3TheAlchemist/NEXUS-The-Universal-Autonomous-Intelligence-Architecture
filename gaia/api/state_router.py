"""
gaia/api/state_router.py
========================
GAIA State API — FastAPI Router
Canon reference: C52, GAIA_D6_META_COHERENCE_ENGINE.md
Issues: #576, #571, #589

Exposes GAIAState and D6Engine via REST + WebSocket.
The Tauri frontend connects to these endpoints for the State HUD.

Endpoints:
  GET  /state              — current GAIAState snapshot
  POST /state              — update specific GAIAState fields
  POST /state/mode         — manually set mode
  POST /state/reset        — reset to default healthy state
  GET  /state/health       — full D6Engine health report (HUD payload)
  POST /state/evaluate     — run D6 evaluation with probes, broadcast result
  GET  /state/interventions — recent intervention log
  POST /state/talisman/activate   — activate a talisman
  POST /state/talisman/deactivate — deactivate a talisman
  WS   /state/ws           — real-time state stream

Wire 1 (Issue #589):
  D6Engine.on_intervention → _on_d6_intervention() → WebSocket broadcast
  Every mode change decision is now emitted as an INTERVENTION_EVENT
  to all connected frontend clients in real time.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from gaia.core.state import GAIAState, GAIAMode, default_state
from gaia.core.d6_engine import D6Engine, EngineProbes, InterventionEvent
from gaia.core.talisman import Talisman, TalismanEngine


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/state", tags=["state"])

# Singleton state and engines for this session.
# In a multi-GAIAN deployment these are keyed by gaian_id/session_id.
_state: GAIAState = default_state()
_talisman_engine: TalismanEngine = TalismanEngine()
_talismans: Dict[str, Talisman] = {}  # id -> Talisman

# WebSocket connection pool
_ws_connections: List[WebSocket] = []


# ---------------------------------------------------------------------------
# Wire 1 — D6Engine.on_intervention callback (Issue #589)
# ---------------------------------------------------------------------------

def _on_d6_intervention(event: InterventionEvent) -> None:
    """
    Callback fired by D6Engine on every intervention event.

    Bridges the synchronous D6Engine into the async WebSocket broadcast loop.
    Uses asyncio.run_coroutine_threadsafe() so it is safe to call from any
    thread (the D6 evaluation may run outside the event loop thread).

    Wire 1 — Issue #589, Phase 1.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        return  # no event loop running — skip (e.g. during unit tests)

    payload = json.dumps({
        "type": "INTERVENTION_EVENT",
        "event": event.to_dict(),
        "t": time.time(),
    })

    async def _send_all(p: str) -> None:
        dead: List[WebSocket] = []
        for ws in list(_ws_connections):
            try:
                await ws.send_text(p)
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in _ws_connections:
                _ws_connections.remove(ws)

    if loop.is_running():
        asyncio.run_coroutine_threadsafe(_send_all(payload), loop)
    else:
        loop.run_until_complete(_send_all(payload))


# D6Engine instantiated WITH the on_intervention callback — Wire 1 is live.
# auto_apply=True: D6 decisions are applied directly to _state.
_engine: D6Engine = D6Engine(
    auto_apply=True,
    on_intervention=_on_d6_intervention,  # ← Wire 1
)


# ---------------------------------------------------------------------------
# Internal broadcast helpers
# ---------------------------------------------------------------------------

async def _broadcast_state() -> None:
    """Push the current GAIAState snapshot to all connected WebSocket clients."""
    if not _ws_connections:
        return
    payload = json.dumps({
        "type": "STATE_UPDATE",
        "state": _state.to_dict(include_history=False),
        "t": time.time(),
    })
    dead: List[WebSocket] = []
    for ws in list(_ws_connections):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        if ws in _ws_connections:
            _ws_connections.remove(ws)


# ---------------------------------------------------------------------------
# Pydantic request/response models
# ---------------------------------------------------------------------------

class StateUpdateRequest(BaseModel):
    energy: Optional[float] = Field(None, ge=0.0, le=1.0)
    coherence: Optional[float] = Field(None, ge=0.0, le=1.0)
    stress: Optional[float] = Field(None, ge=0.0, le=1.0)
    learning_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    exploration_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    conservation_rate: Optional[float] = Field(None, ge=0.0, le=1.0)
    entropy: Optional[float] = Field(None, ge=0.0, le=1.0)


class ModeSetRequest(BaseModel):
    mode: str


class ProbesRequest(BaseModel):
    heart_rate_variability: Optional[float] = None
    sleep_quality: Optional[float] = None
    movement_today: Optional[float] = None
    noosphere_load: Optional[float] = None
    collective_coherence: Optional[float] = None
    schumann_coherence: Optional[float] = None
    lunar_phase_load: Optional[float] = None
    session_duration_hours: Optional[float] = None
    time_since_rest_hours: Optional[float] = None


class TalismanActivateRequest(BaseModel):
    talisman_id: Optional[str] = None
    talisman_data: Optional[Dict[str, Any]] = None
    activated_by: Optional[str] = None


class TalismanDeactivateRequest(BaseModel):
    talisman_id: str
    deactivated_by: Optional[str] = None


# ---------------------------------------------------------------------------
# REST Endpoints
# ---------------------------------------------------------------------------

@router.get("", summary="Get current GAIAState")
async def get_state() -> Dict[str, Any]:
    """Return the current GAIAState snapshot."""
    return _state.to_dict(include_history=False)


@router.post("", summary="Update GAIAState fields")
async def update_state(body: StateUpdateRequest) -> Dict[str, Any]:
    """Apply partial updates to GAIAState. Only provided fields are changed."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update.")
    try:
        _state.update(**updates)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    await _broadcast_state()
    return _state.to_dict(include_history=False)


@router.post("/mode", summary="Manually set operational mode")
async def set_mode(body: ModeSetRequest) -> Dict[str, Any]:
    """Override the current operational mode."""
    try:
        mode = GAIAMode(body.mode)
    except ValueError:
        valid = [m.value for m in GAIAMode]
        raise HTTPException(
            status_code=422,
            detail=f"Invalid mode '{body.mode}'. Valid: {valid}"
        )
    _state.update(mode=mode)
    await _broadcast_state()
    return {"mode": _state.mode.value, "state": _state.to_dict(include_history=False)}


@router.post("/reset", summary="Reset state to healthy baseline")
async def reset_state() -> Dict[str, Any]:
    """Reset GAIAState to default healthy baseline."""
    global _state
    _state = default_state(
        gaian_id=_state.gaian_id,
        session_id=_state.session_id,
    )
    await _broadcast_state()
    return _state.to_dict(include_history=False)


@router.get("/health", summary="D6Engine full health report (HUD payload)")
async def get_health() -> Dict[str, Any]:
    """
    Full D6 Meta-Coherence Engine health report — the primary HUD payload.

    Returns the current state's dimensional health, recommended mode,
    active talisman effects, and recent intervention log.
    No probes are applied — this is a pure READ of current state.
    To evaluate WITH probes, use POST /state/evaluate.
    """
    return _engine.health_report(_state, EngineProbes())


@router.post("/evaluate", summary="Run D6 evaluation with probes, broadcast result")
async def evaluate_with_probes(body: ProbesRequest) -> Dict[str, Any]:
    """
    Run a full D6 evaluation cycle with external probe values.

    Wire 1 (Issue #589): the D6Engine.on_intervention callback fires
    automatically during this call, broadcasting the InterventionEvent
    to all connected WebSocket clients in real time.

    Use this endpoint when:
    - Biometric data arrives from EmbodiedSensorBridge (Wire 2)
    - Noosphere load updates from MotherThread (Wire 3)
    - The frontend HUD polls on a timer (e.g. every 60 seconds)
    - Any subsystem wants to push probe data and trigger a D6 decision
    """
    probes = EngineProbes(**body.model_dump())
    event = _engine.evaluate(_state, probes)
    # If D6 changed the mode (auto_apply=True), broadcast the new state
    if event.auto_applied:
        await _broadcast_state()
    return {
        "event": event.to_dict(),
        "state": _state.to_dict(include_history=False),
        "health": _engine.health_report(_state, probes),
    }


@router.get("/interventions", summary="Recent D6 intervention log")
async def get_interventions(n: int = 20) -> Dict[str, Any]:
    """Return recent D6Engine intervention events."""
    return {
        "interventions": _engine.recent_interventions(n),
        "total": len(_engine.intervention_log),
        "critical_count": len(_engine.critical_interventions()),
    }


@router.post("/talisman/activate", summary="Activate a talisman")
async def activate_talisman(body: TalismanActivateRequest) -> Dict[str, Any]:
    """Activate a talisman by ID or create + activate inline."""
    if body.talisman_id:
        talisman = _talismans.get(body.talisman_id)
        if not talisman:
            raise HTTPException(status_code=404, detail=f"Talisman '{body.talisman_id}' not found.")
    elif body.talisman_data:
        try:
            talisman = Talisman.from_dict(body.talisman_data)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Invalid talisman data: {e}")
        _talismans[talisman.id] = talisman
    else:
        raise HTTPException(status_code=400, detail="Provide talisman_id or talisman_data.")

    event = _talisman_engine.activate(talisman, _state, activated_by=body.activated_by)
    # Re-evaluate D6 after talisman activation so coherence boost is reflected
    # This fires _on_d6_intervention → WebSocket broadcast automatically
    _engine.evaluate(_state)
    await _broadcast_state()
    return {"event": event, "state": _state.to_dict(include_history=False)}


@router.post("/talisman/deactivate", summary="Deactivate a talisman")
async def deactivate_talisman(body: TalismanDeactivateRequest) -> Dict[str, Any]:
    """Deactivate an active talisman."""
    talisman = _talismans.get(body.talisman_id)
    if not talisman:
        raise HTTPException(status_code=404, detail=f"Talisman '{body.talisman_id}' not found.")
    event = _talisman_engine.deactivate(talisman, _state, deactivated_by=body.deactivated_by)
    # Re-evaluate D6 after talisman deactivation
    _engine.evaluate(_state)
    await _broadcast_state()
    return {"event": event, "state": _state.to_dict(include_history=False)}


# ---------------------------------------------------------------------------
# WebSocket — real-time state stream
# ---------------------------------------------------------------------------

@router.websocket("/ws")
async def state_websocket(websocket: WebSocket):
    """
    Real-time state stream for the Tauri frontend State HUD.

    On connect:
      1. Sends STATE_INIT with current state snapshot
      2. Sends HEALTH_INIT with current D6 health report

    Receives JSON messages:
      { "type": "UPDATE", "fields": { ... } }  → partial state update + D6 eval
      { "type": "MODE",   "mode": "BUILD" }    → mode override
      { "type": "PROBE",  "probes": { ... } }  → D6 evaluation with probes
      { "type": "PING" }                        → { "type": "PONG" }

    Emits:
      STATE_INIT         — initial snapshot on connect
      HEALTH_INIT        — initial health report on connect
      STATE_UPDATE       — full state snapshot on any change
      INTERVENTION_EVENT — D6 decision event (via _on_d6_intervention, Wire 1)
      PONG               — response to PING
      ERROR              — malformed message

    Wire 1 (Issue #589): INTERVENTION_EVENT messages are now emitted
    automatically by _on_d6_intervention() on every D6 evaluation,
    independent of the message handler below. The HUD is live.
    """
    await websocket.accept()
    _ws_connections.append(websocket)

    # Send initial snapshots
    await websocket.send_text(json.dumps({
        "type": "STATE_INIT",
        "state": _state.to_dict(include_history=False),
        "t": time.time(),
    }))
    await websocket.send_text(json.dumps({
        "type": "HEALTH_INIT",
        "health": _engine.health_report(_state, EngineProbes()),
        "t": time.time(),
    }))

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "ERROR", "detail": "Invalid JSON"}))
                continue

            msg_type = msg.get("type", "")

            if msg_type == "PING":
                await websocket.send_text(json.dumps({"type": "PONG", "t": time.time()}))

            elif msg_type == "UPDATE":
                updates = {k: v for k, v in msg.get("fields", {}).items() if v is not None}
                if updates:
                    try:
                        _state.update(**updates)
                        # Wire 1: evaluate triggers _on_d6_intervention → broadcast
                        _engine.evaluate(_state)
                        await _broadcast_state()
                    except (ValueError, AttributeError) as e:
                        await websocket.send_text(json.dumps({"type": "ERROR", "detail": str(e)}))

            elif msg_type == "MODE":
                try:
                    mode = GAIAMode(msg.get("mode", ""))
                    _state.update(mode=mode)
                    _engine.evaluate(_state)
                    await _broadcast_state()
                except ValueError:
                    await websocket.send_text(json.dumps({
                        "type": "ERROR",
                        "detail": f"Invalid mode: {msg.get('mode')}"
                    }))

            elif msg_type == "PROBE":
                # Wire 1+2+3: frontend can push probe data directly over WS
                # D6 evaluates immediately, _on_d6_intervention broadcasts result
                try:
                    probe_data = msg.get("probes", {})
                    probes = EngineProbes(**{k: v for k, v in probe_data.items() if v is not None})
                    event = _engine.evaluate(_state, probes)
                    if event.auto_applied:
                        await _broadcast_state()
                except Exception as e:
                    await websocket.send_text(json.dumps({"type": "ERROR", "detail": str(e)}))

            else:
                await websocket.send_text(json.dumps({
                    "type": "UNKNOWN",
                    "detail": f"Unknown message type: {msg_type}"
                }))

    except WebSocketDisconnect:
        if websocket in _ws_connections:
            _ws_connections.remove(websocket)
