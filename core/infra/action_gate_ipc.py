"""
core/infra/action_gate_ipc.py

IPC callback layer for ActionGate — emits action-gate-confirm events
to the Tauri WebView so the human sovereign can approve / deny actions.

Emit path (production):
  _emit_ipc()  →  POST http://127.0.0.1:8009/emit  →  Axum IPC bridge
               →  tauri AppHandle.emit()  →  WebView CustomEvent

Emit path (fallback / dev without Tauri):
  _emit_ipc()  →  structured WARNING log  →  frontend log-bridge parser

The IPC bridge comes online when Rust calls POST /internal/ipc-ready on
the FastAPI backend.  Until that signal arrives the flag _ipc_bridge_ready
is False and all emits fall through to the log-bridge path.

Canon: Doc 35 (Security), Doc 21 (Sovereignty)
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

log = logging.getLogger(__name__)

# ── State ────────────────────────────────────────────────────────────────────

_ipc_bridge_ready: bool = False   # set True when Rust calls /internal/ipc-ready
_IPC_BRIDGE_URL   = "http://127.0.0.1:8009/emit"
_IPC_TIMEOUT_S    = 2.0


def mark_ipc_bridge_ready() -> None:
    """Called by the /internal/ipc-ready FastAPI endpoint."""
    global _ipc_bridge_ready
    _ipc_bridge_ready = True
    log.info("[ActionGate IPC] Axum bridge ready — using native Tauri emit path.")


# ── Core emit ────────────────────────────────────────────────────────────────

async def _emit_ipc(event: str, payload: dict[str, Any]) -> None:
    """Emit an event to the Tauri WebView.

    Tries the Axum IPC bridge first; falls back to the structured log
    bridge if the bridge is not yet ready or the POST fails.
    """
    if _ipc_bridge_ready:
        try:
            async with httpx.AsyncClient(timeout=_IPC_TIMEOUT_S) as client:
                resp = await client.post(
                    _IPC_BRIDGE_URL,
                    json={"event": event, "payload": payload},
                )
                if resp.status_code == 200:
                    log.debug("[ActionGate IPC] emitted %s via Axum bridge", event)
                    return
                log.warning(
                    "[ActionGate IPC] bridge returned %s — falling back to log-bridge",
                    resp.status_code,
                )
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "[ActionGate IPC] bridge POST failed (%s) — falling back to log-bridge",
                exc,
            )

    # ── Log-bridge fallback (dev / pre-bridge) ────────────────────────────
    import json
    log.warning("[TAURI_IPC] %s %s", event, json.dumps(payload))


# ── Confirm callback (wired into ActionGate at startup) ───────────────────────

async def _ipc_confirm_callback(
    request_id: str,
    tier: str,
    action_type: str,
    description: str,
    timeout: int,
    default: bool,
    resolve_event: asyncio.Event,
    result_holder: list[bool],
) -> bool:
    """Emit a gate event to the WebView, then wait for the sovereign to respond.

    The FastAPI endpoint POST /action-gate/respond resolves the asyncio.Event
    and sets result_holder[0] when the human clicks Approve / Deny.
    """
    payload: dict[str, Any] = {
        "request_id":  request_id,
        "tier":        tier,
        "type":        action_type,
        "description": description,
        "timeout":     timeout,
        "default":     default,
    }

    await _emit_ipc("action-gate-confirm", payload)

    try:
        await asyncio.wait_for(resolve_event.wait(), timeout=float(timeout))
        return result_holder[0]
    except asyncio.TimeoutError:
        log.warning(
            "[ActionGate IPC] request %s timed out — applying default (%s)",
            request_id, default,
        )
        return default


def get_ipc_confirm_callback():
    """Return the confirm callback for wiring into ActionGate._confirm_callback."""
    return _ipc_confirm_callback
