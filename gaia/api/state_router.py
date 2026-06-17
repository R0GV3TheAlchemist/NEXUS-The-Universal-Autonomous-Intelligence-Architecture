"""
gaia/api/state_router.py

REST + WebSocket surface for GAIAState and the D6 Meta-Coherence Engine.

Canon anchors:
  - GAIA_D6_META_COHERENCE_ENGINE.md  (sealed 2026-06-17)
  - Issue #568  (D6 Meta-Coherence Engine)
  - Issue #576  (GAIAState — central state object)
  - Issue #578  (Architect Protocol — GOVERNANCE always first)
  - Issue #580  (Talisman Object — active_talismans)

Endpoints
---------
  GET  /state                  Full D6 runtime JSON snapshot
  GET  /state/mode             Lightweight mode + color poll (front-end HUD)
  POST /state/update           Push probe updates → D6 runs → returns decision
  POST /state/transition       Request a specific mode change via D6
  POST /state/governance       Architect override → immediate GOVERNANCE mode
  POST /state/unlock           Unlock PROTECT mode (Architect confirmation)
  WS   /state/stream           Live push: D6 snapshot every 5s + on transition

Design rules:
  - ALL writes route through state_store.run_d6_cycle() — D6 always runs.
  - GOVERNANCE override is a dedicated endpoint, never gated by coherence.
  - PROTECT mode can only be exited via /state/unlock or /state/governance.
  - WebSocket stream is the primary feed for the front-end State HUD.
  - No raw field mutation is exposed — all changes go through D6.

For the Good and the Greater Good.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect, status
from pydantic import BaseModel, Field, field_validator

from gaia.core.state import GAIAOperationalMode
from gaia.core.d6_engine import D6Inputs, compute_next_state, clamp
from gaia.core import state_store


router = APIRouter()


# ── Pydantic Models ─────────────────────────────────────────────────────

class ProbeUpdateRequest(BaseModel):
    """Push updated probe values to GAIAState.

    Only fields you include will be updated; others retain their
    current value in the store. All float values clamped to [0.0, 1.0].
    """
    # Dimensional health probes (D1–D5)
    d1_health: Optional[float] = Field(None, ge=0.0, le=1.0)
    d2_health: Optional[float] = Field(None, ge=0.0, le=1.0)
    d3_health: Optional[float] = Field(None, ge=0.0, le=1.0)
    d4_health: Optional[float] = Field(None, ge=0.0, le=1.0)
    d5_health: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Scalar state
    energy:              Optional[float] = Field(None, ge=0.0, le=1.0)
    stress:              Optional[float] = Field(None, ge=0.0, le=1.0)
    entropy:             Optional[float] = Field(None, ge=0.0, le=1.0)
    personal_coherence:  Optional[float] = Field(None, ge=0.0, le=1.0)
    noosphere_load:      Optional[float] = Field(None, ge=0.0, le=1.0)

    # Temporal / talisman
    cycle_position:      Optional[int]        = Field(None, ge=1)
    epoch:               Optional[str]        = None
    active_talismans:    Optional[list[str]]  = None
    special_conditions:  Optional[list[str]]  = None

    # Optional richer D6 inputs
    recent_error_rate:   Optional[float] = Field(None, ge=0.0, le=1.0)
    session_hours:       Optional[float] = Field(None, ge=0.0)
    new_data_present:    Optional[bool]  = None
    threat_detected:     Optional[bool]  = None


class ModeTransitionRequest(BaseModel):
    """Request a specific mode change.

    D6 will validate whether conditions support the requested mode.
    If not, D6 will select the appropriate mode and explain why.
    Exception: GOVERNANCE is always honoured (use /state/governance).
    """
    requested_mode: str = Field(
        ...,
        description="One of: research, build, learn, reflect, recover, protect, governance",
    )
    reason: Optional[str] = Field(None, description="Optional human note for the log")

    @field_validator("requested_mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        valid = {m.value for m in GAIAOperationalMode}
        if v.lower() not in valid:
            raise ValueError(f"Invalid mode '{v}'. Valid modes: {sorted(valid)}")
        return v.lower()


class GovernanceRequest(BaseModel):
    """Architect override — immediately sets GOVERNANCE mode.

    No coherence check. No stress check. No threshold.
    The human comes first. (Issue #578 — Architect Protocol)
    """
    reason: Optional[str] = Field(
        None,
        description="Optional reason for the governance override",
    )
    session_id: Optional[str] = Field(None, description="Active session ID")


class UnlockRequest(BaseModel):
    """Architect confirmation to unlock PROTECT mode.

    Only the Architect can unlock PROTECT. D6 will re-evaluate
    state after unlock and assign the appropriate recovery mode.
    """
    confirmation: str = Field(
        ...,
        description="Must be exactly: 'ARCHITECT_CONFIRMS_RECOVERY'",
    )
    reason: Optional[str] = Field(None, description="Optional recovery note")

    @field_validator("confirmation")
    @classmethod
    def validate_confirmation(cls, v: str) -> str:
        if v != "ARCHITECT_CONFIRMS_RECOVERY":
            raise ValueError(
                "Confirmation token must be exactly: 'ARCHITECT_CONFIRMS_RECOVERY'"
            )
        return v


class D6StateResponse(BaseModel):
    """Full D6 runtime JSON response.

    Mirrors the canonical schema from GAIA_D6_META_COHERENCE_ENGINE.md Part VI.
    """
    system_state:                str
    mode_color:                  str
    mode_locked:                 bool
    architect_override_available: bool
    d1_health:                   float
    d2_health:                   float
    d3_health:                   float
    d4_health:                   float
    d5_health:                   float
    coherence:                   float
    phi:                         float
    intervention_needed:         bool
    energy:                      float
    stress:                      float
    entropy:                     float
    learning_rate:               float
    exploration_rate:            float
    conservation_rate:           float
    adaptation:                  float
    personal_coherence:          float
    noosphere_load:              float
    cycle_position:              int
    epoch:                       str
    circadian_band:              str
    special_conditions:          list[str]
    active_talismans:            list[str]
    high_risk_allowed:           bool
    canon_write_allowed:         bool
    last_transition_at:          str
    session_id:                  str


class ModeResponse(BaseModel):
    """Lightweight mode response for front-end HUD polling."""
    system_state:     str
    mode_color:       str
    coherence:        float
    phi:              float
    mode_locked:      bool
    intervention_needed: bool
    circadian_band:   str
    timestamp:        str


class DecisionResponse(BaseModel):
    """D6 decision response — returned after any state mutation."""
    state:          D6StateResponse
    interventions:  list[str]
    rationale:      str
    mode_changed:   bool
    timestamp:      str


# ── WebSocket connection manager ────────────────────────────────────────────

class _WSConnectionManager:
    """Manages active WebSocket connections for the /state/stream endpoint."""

    def __init__(self) -> None:
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self._connections = [c for c in self._connections if c is not ws]

    async def broadcast(self, payload: dict) -> None:
        """Send a JSON payload to all connected clients."""
        message = json.dumps(payload)
        dead: list[WebSocket] = []
        for ws in self._connections:
            try:
                await ws.send_text(message)
            except Exception:  # noqa: BLE001
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)

    @property
    def active_connections(self) -> int:
        return len(self._connections)


_ws_manager = _WSConnectionManager()


# ── Internal helpers ──────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _state_to_response(runtime_json: dict[str, Any]) -> D6StateResponse:
    """Convert a to_runtime_json() dict into a typed D6StateResponse."""
    return D6StateResponse(**runtime_json)


async def _broadcast_state() -> None:
    """Broadcast current state to all WS subscribers."""
    payload = state_store.get_runtime_json()
    payload["_event"] = "state_update"
    payload["_ws_clients"] = _ws_manager.active_connections
    await _ws_manager.broadcast(payload)


def _build_decision_response(
    decision: Any,
    previous_mode: str,
) -> DecisionResponse:
    """Build a DecisionResponse from a D6Decision."""
    runtime = decision.next_state.to_runtime_json()
    return DecisionResponse(
        state=D6StateResponse(**runtime),
        interventions=decision.interventions,
        rationale=decision.rationale,
        mode_changed=runtime["system_state"] != previous_mode,
        timestamp=_now_iso(),
    )


# ── Routes ──────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=D6StateResponse,
    summary="Full GAIAState snapshot",
    description=(
        "Returns the complete D6 runtime JSON: all dimensional probes, "
        "mode, coherence, phi, talismans, circadian band, temporal context, "
        "and all gate flags. Primary read endpoint for the State HUD."
    ),
)
async def get_state() -> D6StateResponse:
    """GET /state — Full D6 runtime snapshot."""
    return _state_to_response(state_store.get_runtime_json())


@router.get(
    "/mode",
    response_model=ModeResponse,
    summary="Lightweight mode poll",
    description=(
        "Returns only the current mode, color, coherence, phi, and key flags. "
        "Use this for front-end HUD polling (low bandwidth, high frequency)."
    ),
)
async def get_mode() -> ModeResponse:
    """GET /state/mode — Lightweight mode + coherence snapshot."""
    s = state_store.get_state()
    return ModeResponse(
        system_state=s.mode.value,
        mode_color=s.to_runtime_json()["mode_color"],
        coherence=round(s.harmonic_coherence(), 4),
        phi=round(s.phi, 4),
        mode_locked=s.mode_locked,
        intervention_needed=s.intervention_needed(),
        circadian_band=s.circadian_band,
        timestamp=_now_iso(),
    )


@router.post(
    "/update",
    response_model=DecisionResponse,
    summary="Push probe updates → D6 runs → returns decision",
    description=(
        "Update one or more GAIAState probe values. D6 always runs after any "
        "update — the returned decision contains the new mode, all interventions, "
        "and a rationale string. Only fields included in the request body are updated."
    ),
)
async def update_state(body: ProbeUpdateRequest) -> DecisionResponse:
    """POST /state/update — Push probes, run D6, return decision."""
    previous_mode = state_store.get_state().mode.value

    # Apply all probe updates to a fresh copy and run D6
    from copy import deepcopy
    updated = deepcopy(state_store.get_state())

    if body.d1_health      is not None: updated.d1_health      = clamp(body.d1_health)
    if body.d2_health      is not None: updated.d2_health      = clamp(body.d2_health)
    if body.d3_health      is not None: updated.d3_health      = clamp(body.d3_health)
    if body.d4_health      is not None: updated.d4_health      = clamp(body.d4_health)
    if body.d5_health      is not None: updated.d5_health      = clamp(body.d5_health)
    if body.energy         is not None: updated.energy         = clamp(body.energy)
    if body.stress         is not None: updated.stress         = clamp(body.stress)
    if body.entropy        is not None: updated.entropy        = clamp(body.entropy)
    if body.personal_coherence is not None:
        updated.personal_coherence = clamp(body.personal_coherence)
    if body.noosphere_load is not None: updated.noosphere_load = clamp(body.noosphere_load)
    if body.cycle_position     is not None: updated.cycle_position     = body.cycle_position
    if body.epoch              is not None: updated.epoch              = body.epoch
    if body.active_talismans   is not None: updated.active_talismans   = body.active_talismans
    if body.special_conditions is not None: updated.special_conditions = body.special_conditions

    inputs = D6Inputs(
        current_state=updated,
        recent_error_rate=body.recent_error_rate,
        session_hours=body.session_hours,
        new_data_present=body.new_data_present or False,
        threat_detected=body.threat_detected or False,
    )
    decision = compute_next_state(inputs)
    state_store.set_state(decision.next_state)

    # Broadcast to all WebSocket subscribers
    await _broadcast_state()

    return _build_decision_response(decision, previous_mode)


@router.post(
    "/transition",
    response_model=DecisionResponse,
    summary="Request a mode transition via D6",
    description=(
        "Request a specific operational mode. D6 validates whether current "
        "conditions support the requested mode. If not, D6 assigns the appropriate "
        "mode and returns its rationale. GOVERNANCE is always honoured — "
        "use /state/governance for the dedicated Architect override."
    ),
)
async def request_transition(body: ModeTransitionRequest) -> DecisionResponse:
    """POST /state/transition — Request mode change via D6."""
    previous_mode = state_store.get_state().mode.value

    requested = GAIAOperationalMode(body.requested_mode)

    # GOVERNANCE requests route to the dedicated path
    if requested == GAIAOperationalMode.GOVERNANCE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use POST /state/governance for Architect override. "
                   "GOVERNANCE mode is always available there.",
        )

    # mode_locked check — only GOVERNANCE can exit PROTECT while locked
    current = state_store.get_state()
    if current.mode_locked and current.mode == GAIAOperationalMode.PROTECT:
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="PROTECT mode is locked. Use POST /state/unlock to confirm "
                   "recovery, or POST /state/governance for immediate override.",
        )

    decision = state_store.request_mode_change(requested)
    await _broadcast_state()
    return _build_decision_response(decision, previous_mode)


@router.post(
    "/governance",
    response_model=DecisionResponse,
    status_code=status.HTTP_200_OK,
    summary="Architect override — immediate GOVERNANCE mode",
    description=(
        "Immediately sets GOVERNANCE mode regardless of coherence, stress, "
        "or mode_locked status. The human comes first. "
        "(Issue #578 — Architect Protocol)"
    ),
)
async def architect_governance_override(body: GovernanceRequest) -> DecisionResponse:
    """POST /state/governance — Architect override, no threshold check."""
    previous_mode = state_store.get_state().mode.value

    from copy import deepcopy
    current = deepcopy(state_store.get_state())
    if body.session_id:
        current.session_id = body.session_id

    inputs = D6Inputs(
        current_state=current,
        architect_request=True,  # always triggers GOVERNANCE in D6 engine
    )
    decision = compute_next_state(inputs)
    state_store.set_state(decision.next_state)

    await _broadcast_state()

    reason_note = f" Reason: {body.reason}" if body.reason else ""
    decision.interventions.insert(
        0, f"Architect governance override activated.{reason_note}"
    )

    return _build_decision_response(decision, previous_mode)


@router.post(
    "/unlock",
    response_model=DecisionResponse,
    summary="Unlock PROTECT mode (Architect confirmation)",
    description=(
        "Unlocks PROTECT mode after Architect confirms recovery. "
        "Requires the confirmation token 'ARCHITECT_CONFIRMS_RECOVERY'. "
        "D6 re-evaluates state post-unlock and assigns appropriate mode."
    ),
)
async def unlock_protect(body: UnlockRequest) -> DecisionResponse:
    """POST /state/unlock — Architect confirmation to exit PROTECT."""
    current = state_store.get_state()

    if not current.mode_locked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State is not locked. Nothing to unlock.",
        )

    previous_mode = current.mode.value

    from copy import deepcopy
    unlocked = deepcopy(current)
    unlocked.mode_locked = False  # remove the lock before D6 re-evaluates

    inputs = D6Inputs(current_state=unlocked)
    decision = compute_next_state(inputs)
    state_store.set_state(decision.next_state)

    await _broadcast_state()

    reason_note = f" Reason: {body.reason}" if body.reason else ""
    decision.interventions.insert(
        0, f"PROTECT mode unlocked by Architect.{reason_note} D6 re-evaluated."
    )

    return _build_decision_response(decision, previous_mode)


@router.websocket("/stream")
async def state_stream(websocket: WebSocket) -> None:
    """WS /state/stream — Live D6 state push.

    Immediately sends the current state on connect, then:
      - Pushes a full D6 snapshot every 5 seconds.
      - Receives JSON messages from the client:
          {"ping": true}           → pong response
          {"request_refresh": true} → immediate state push

    Front-end State HUD subscribes here for live mode + coherence updates.
    """
    await _ws_manager.connect(websocket)
    try:
        # Send immediate state on connect
        payload = state_store.get_runtime_json()
        payload["_event"] = "connected"
        payload["_ws_clients"] = _ws_manager.active_connections
        await websocket.send_text(json.dumps(payload))

        while True:
            try:
                # Non-blocking receive with 5s timeout — drives the heartbeat
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=5.0)
                msg = json.loads(raw)

                if msg.get("ping"):
                    await websocket.send_text(json.dumps({
                        "_event": "pong",
                        "timestamp": _now_iso(),
                    }))

                elif msg.get("request_refresh"):
                    refresh_payload = state_store.get_runtime_json()
                    refresh_payload["_event"] = "refresh"
                    await websocket.send_text(json.dumps(refresh_payload))

            except asyncio.TimeoutError:
                # 5s heartbeat — push current state to this client
                heartbeat = state_store.get_runtime_json()
                heartbeat["_event"] = "heartbeat"
                heartbeat["_ws_clients"] = _ws_manager.active_connections
                await websocket.send_text(json.dumps(heartbeat))

    except WebSocketDisconnect:
        _ws_manager.disconnect(websocket)
    except Exception:  # noqa: BLE001
        _ws_manager.disconnect(websocket)
