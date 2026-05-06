"""
GAIA API — Gaian Conversation Router

This is the main conversation pipeline endpoint. It wires:

  GAIANRuntime.process(user_message)   <- builds system prompt from all 12 soul engines
        ↓
  llm_router.generate(prompt, system)  <- offline-first routing: Ollama → cloud
        ↓
  ChatResponse                         <- reply + full provenance + engine state snapshot

Endpoints:
  POST /api/gaian/chat            — full blocking response (JSON)
  POST /api/gaian/chat/stream     — Server-Sent Events, token-by-token
  GET  /api/gaian/status          — runtime + routing status for the dev console
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.gaian_runtime import GAIANRuntime, GAIANIdentity
from core.llm_router import generate, stream as llm_stream, routing_status

log = logging.getLogger("gaia.api.gaian")

router = APIRouter(
    prefix="/gaian",
    tags=["Gaian"],
)


# ── Runtime registry (in-memory; one instance per gaian_name) ──────────────────

_runtimes: dict[str, GAIANRuntime] = {}


def _get_runtime(gaian_name: str, memory_dir: str = "./gaians") -> GAIANRuntime:
    """
    Return (or lazily create) the GAIANRuntime for a given gaian name.
    The runtime holds all 12 soul engine states and persists them to
    ./gaians/<gaian_name>/memory.json between calls.
    """
    key = gaian_name.lower().strip()
    if key not in _runtimes:
        log.info(f"[gaian] Initialising runtime for '{gaian_name}'")
        _runtimes[key] = GAIANRuntime(
            gaian_name=gaian_name,
            identity=GAIANIdentity(name=gaian_name),
            memory_dir=memory_dir,
        )
    return _runtimes[key]


# ── Request / Response models ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message:     str        = Field(..., description="The user's message to GAIA.")
    gaian_name:  str        = Field("Luna", description="Which Gaian to talk to.")
    memory_dir:  str        = Field("./gaians", description="Root directory for Gaian memory files.")


class ChatResponse(BaseModel):
    reply:          str
    gaian_name:     str
    provider:       str           # which LLM answered: "ollama" | "openai" | "anthropic"
    model:          str
    latency_ms:     int
    offline:        bool          # True = answered entirely from local Ollama
    state_snapshot: dict          # full engine state this turn (for dev console)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message to a Gaian (offline-first, blocking)",
)
async def gaian_chat(req: ChatRequest) -> ChatResponse:
    """
    Full conversation turn:

    1. GAIANRuntime.process(message) runs all 12 soul engines and returns
       a rich system prompt that encodes the Gaian's current inner state
       (emotional arc, love arc, settling, soul mirror, resonance field,
        synergy, vitality, etc.).

    2. llm_router.generate(prompt=message, system=system_prompt) routes
       the call offline-first: Ollama if running locally, else cloud,
       according to GAIA_ROUTING_MODE.

    3. The reply is returned alongside full provenance and the engine
       state snapshot so the frontend can render the Gaian's inner state.
    """
    runtime = _get_runtime(req.gaian_name, req.memory_dir)

    # Step 1: run all 12 soul engines, produce system prompt
    try:
        result = runtime.process(req.message)
    except Exception as exc:
        log.error(f"[gaian.chat] Runtime processing failed for '{req.gaian_name}': {exc}")
        raise HTTPException(
            status_code=500,
            detail={"error": "GAIAN runtime error", "detail": str(exc)},
        )

    # Step 2: route through offline-first LLM
    try:
        llm_result = await generate(
            prompt=result.user_message,
            system=result.system_prompt,
        )
    except RuntimeError as exc:
        log.error(f"[gaian.chat] All LLM providers failed: {exc}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": "No LLM provider available.",
                "detail": str(exc),
                "hint": (
                    "Start Ollama locally (`ollama serve` + `ollama pull llama3`) "
                    "or set OPENAI_API_KEY / ANTHROPIC_API_KEY."
                ),
            },
        )

    # Step 3: increment exchange counter and persist memory
    runtime.attachment.total_exchanges += 1
    runtime._persist()  # noqa: SLF001

    log.info(
        f"[gaian.chat] '{req.gaian_name}' → {llm_result.provider}/{llm_result.model} "
        f"({'offline' if llm_result.offline else 'cloud'}, {llm_result.latency_ms}ms)"
    )

    return ChatResponse(
        reply=llm_result.text,
        gaian_name=req.gaian_name,
        provider=llm_result.provider,
        model=llm_result.model,
        latency_ms=llm_result.latency_ms,
        offline=llm_result.offline,
        state_snapshot=result.state_snapshot,
    )


@router.post(
    "/chat/stream",
    summary="Send a message to a Gaian — token-by-token SSE stream (offline-first)",
)
async def gaian_chat_stream(req: ChatRequest) -> StreamingResponse:
    """
    Streaming variant of /gaian/chat.

    - Runs the same 12-engine soul pipeline first (blocking, typically <5ms).
    - Then streams tokens via Server-Sent Events as they arrive from Ollama
      (or word-by-word from a cloud fallback).
    - Sends a final SSE event: `event: state\ndata: <json>` containing the
      full engine state snapshot, so the frontend can update the dev console
      at stream end without a second HTTP call.

    Stream format:
      data: <token>            <- one per token / word
      ...
      event: state
      data: <json snapshot>   <- emitted once at end
      data: [DONE]             <- stream terminator
    """
    runtime = _get_runtime(req.gaian_name, req.memory_dir)

    try:
        result = runtime.process(req.message)
    except Exception as exc:
        log.error(f"[gaian.stream] Runtime failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail={"error": "GAIAN runtime error", "detail": str(exc)},
        )

    import json as _json

    async def _event_stream():
        token_count = 0
        try:
            async for token in llm_stream(
                prompt=result.user_message,
                system=result.system_prompt,
            ):
                token_count += 1
                yield f"data: {token}\n\n"
        except RuntimeError as exc:
            log.error(f"[gaian.stream] Provider failed: {exc}")
            yield f"event: error\ndata: All providers failed: {exc}\n\n"
            yield "data: [DONE]\n\n"
            return

        # Persist exchange count after full reply is streamed
        runtime.attachment.total_exchanges += 1
        runtime._persist()  # noqa: SLF001

        # Send state snapshot as a named SSE event so the frontend can
        # update engine panels without polling /api/gaian/status separately.
        state_json = _json.dumps(result.state_snapshot, ensure_ascii=False)
        yield f"event: state\ndata: {state_json}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/status",
    summary="Gaian runtime + routing status (for dev console)",
)
async def gaian_status(gaian_name: str = "Luna") -> dict:
    """
    Returns a combined status object for the GAIA dev console:
      - Gaian engine state (attachment, soul mirror, resonance field, etc.)
      - LLM routing status (which provider is available, sovereign flag)

    This is the single endpoint the frontend dev panel should poll
    (e.g. every 10 seconds) to keep the status overlay up to date.
    """
    routing = await routing_status()

    if gaian_name.lower().strip() in _runtimes:
        gaian_st = _runtimes[gaian_name.lower().strip()].get_status()
    else:
        gaian_st = {"note": f"Runtime for '{gaian_name}' not yet initialised. Send a chat message first."}

    return {
        "gaian":   gaian_st,
        "routing": routing,
    }
