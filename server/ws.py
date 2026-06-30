"""
GAIA OS WebSocket endpoints.

The /v1/ws/talk/{gaian_id} endpoint provides a live,
bidirectional conversation channel with a GAIAN.

Protocol:
  Client sends: JSON  { "content": "...", "human_id": "..." }
  Server sends: JSON  { "response": "...", "turn": N,
                        "cognitive_state": {...}, "ended": false }
  Client sends: empty content or { "content": "" } to end the session.
  Server sends: { "ended": true, "turns": N } as final message.

Auth:
  The Bearer token in the HTTP Upgrade request headers is extracted
  by BearerAuthMiddleware before the WebSocket handshake. The
  caller_id flows through to the GAIAOSApi as usual.

Error handling:
  All errors are sent as JSON { "error": "...", "code": "..." }
  before closing the WebSocket with code 1011 (internal error)
  or 1008 (policy violation / autonomy violation).
"""
from __future__ import annotations

import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.api.api import APIErrorCode, APIRequest

ws_router = APIRouter()


@ws_router.websocket("/v1/ws/talk/{gaian_id}")
async def ws_talk(websocket: WebSocket, gaian_id: str):
    """
    Live bidirectional conversation with a GAIAN over WebSocket.

    The session is opened on connect, one turn per message,
    and closed when the client sends empty content or disconnects.
    """
    await websocket.accept()

    api = websocket.app.state.api
    caller_id = getattr(websocket.state, "caller_id", "ws-anonymous")

    # Begin session
    begin_resp = api.dispatch(APIRequest(
        caller_id=caller_id,
        endpoint="/v1/session/begin",
        payload={"gaian_id": gaian_id, "human_id": caller_id},
    ))
    if not begin_resp.success:
        await websocket.send_json({
            "error": begin_resp.message,
            "code": begin_resp.code.value,
        })
        await websocket.close(code=1011)
        return

    session_id = begin_resp.payload.get("session_id", "")

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = {"content": raw}

            content = data.get("content", "").strip()
            if not content:
                break  # client ending session

            human_id = data.get("human_id", caller_id)

            turn_resp = api.dispatch(APIRequest(
                caller_id=caller_id,
                endpoint="/v1/session/turn",
                payload={
                    "gaian_id": gaian_id,
                    "content": content,
                    "human_id": human_id,
                    "modality": data.get("modality", "text"),
                },
            ))

            if not turn_resp.success:
                if turn_resp.code == APIErrorCode.AUTONOMY_VIOLATION:
                    await websocket.send_json({
                        "error": turn_resp.message,
                        "code": turn_resp.code.value,
                    })
                    await websocket.close(code=1008)  # policy violation
                    return
                await websocket.send_json({
                    "error": turn_resp.message,
                    "code": turn_resp.code.value,
                })
                continue

            await websocket.send_json({
                "response": turn_resp.payload.get("response", ""),
                "turn": turn_resp.payload.get("turn", 0),
                "cognitive_state": turn_resp.payload.get("cognitive_state", {}),
                "session_id": session_id,
                "ended": False,
            })

    except WebSocketDisconnect:
        pass

    finally:
        # Always try to end the session cleanly
        end_resp = api.dispatch(APIRequest(
            caller_id=caller_id,
            endpoint="/v1/session/end",
            payload={"gaian_id": gaian_id},
        ))
        turns = end_resp.payload.get("turns", 0) if end_resp.success else 0
        try:
            await websocket.send_json({
                "ended": True,
                "turns": turns,
                "session_id": session_id,
            })
        except Exception:
            pass
