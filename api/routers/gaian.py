"""
GAIA API — Gaian Conversation Router

Endpoints
---------
POST /api/gaians/{slug}/chat      — SSE stream (GaiaChat.tsx primary path)
POST /api/gaian/chat              — blocking JSON  (legacy / curl testing)
POST /api/gaian/chat/stream       — SSE stream     (legacy)
GET  /api/gaian/status            — runtime + routing status

Memory context
--------------
When the frontend passes `memory_context` in the request body, this router
injects it into the system prompt between the soul-engine block and the
LLM call.  The injection is a no-op when the field is absent or empty.
"""

from __future__ import annotations

import json as _json
import logging
import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from core.gaian_runtime import GAIANRuntime, GAIANIdentity
from core.llm_router import generate, stream as llm_stream, routing_status

log = logging.getLogger("gaia.api.gaian")

router = APIRouter(tags=["Gaian"])


# ── Runtime registry ──────────────────────────────────────────────────────────────────────────────────

_runtimes: dict[str, GAIANRuntime] = {}


def _get_runtime(gaian_name: str, memory_dir: str = "./gaians") -> GAIANRuntime:
    key = gaian_name.lower().strip()
    if key not in _runtimes:
        log.info("[gaian] Initialising runtime for '%s'", gaian_name)
        _runtimes[key] = GAIANRuntime(
            gaian_name=gaian_name,
            identity=GAIANIdentity(name=gaian_name),
            memory_dir=memory_dir,
        )
    return _runtimes[key]


# ── Memory context injection helper ───────────────────────────────────────────────

def _inject_memory(system_prompt: str, memory_context: Optional[str]) -> str:
    """
    Append the memory context block to the system prompt.

    The block is already formatted by the frontend's promptMemory.ts:

        <GAIA_MEMORY>
        [1] (preference, importance=0.90) I prefer dark mode
        ...
        </GAIA_MEMORY>

    We honour whatever the frontend sends verbatim.  If `memory_context`
    is None, empty, or already present in the prompt, we skip injection.
    """
    if not memory_context or not memory_context.strip():
        return system_prompt
    if "<GAIA_MEMORY>" in system_prompt:
        return system_prompt   # already injected upstream
    return f"{system_prompt}\n\n{memory_context.strip()}"


# ── Pydantic models ─────────────────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    """Legacy model (POST /api/gaian/chat)."""
    message:        str  = Field(...)
    gaian_name:     str  = Field("Luna")
    memory_dir:     str  = Field("./gaians")
    memory_context: Optional[str] = Field(None, description="Pre-formatted <GAIA_MEMORY> block.")


class ChatRequestV2(BaseModel):
    """
    Request body for POST /api/gaians/{slug}/chat.
    Matches exactly what GaiaChat.tsx sends.
    """
    message:           str            = Field(...)
    session_id:        Optional[str]  = None
    enable_web_search: bool           = False
    schumann_hz:       float          = Field(7.83)
    mode:              str            = Field("control")
    memory_context:    Optional[str]  = Field(
        None,
        description="<GAIA_MEMORY> block built by the frontend promptMemory.ts."
    )


class ChatResponse(BaseModel):
    reply:          str
    gaian_name:     str
    provider:       str
    model:          str
    latency_ms:     int
    offline:        bool
    state_snapshot: dict


# ── PRIMARY ENDPOINT: /api/gaians/{slug}/chat  (GaiaChat.tsx → here) ────────

@router.post(
    "/gaians/{slug}/chat",
    summary="GAIA primary chat — SSE token stream (GaiaChat.tsx)",
)
async def gaians_slug_chat(slug: str, req: ChatRequestV2) -> StreamingResponse:
    """
    Primary conversation endpoint consumed by GaiaChat.tsx.

    SSE event format
    ----------------
    event: token
    data: {"text": "<token>"}

    event: done
    data: {
      "epistemic_label":  str,
      "backend_used":     str,
      "bond_depth":       float,
      "canon_docs":       int,
      "inference_ms":     int
    }

    event: error
    data: {"error": "<message>"}

    Memory context
    --------------
    When `memory_context` is present in the request body, it is appended to
    the soul-engine system prompt before the LLM call so GAIA can reference
    past conversations, preferences, and facts about the user.
    """
    runtime = _get_runtime(slug)
    t0 = time.perf_counter()

    # ─ Step 1: run all soul engines ─────────────────────────────────────────────────────
    try:
        result = runtime.process(req.message)
    except Exception as exc:
        log.error("[gaians/%s] Runtime failed: %s", slug, exc)
        raise HTTPException(
            status_code=500,
            detail={"error": "GAIAN runtime error", "detail": str(exc)},
        )

    # ─ Step 2: inject memory context into system prompt ───────────────────
    system_prompt = _inject_memory(result.system_prompt, req.memory_context)
    mem_hit_count = req.memory_context.count("[" ) if req.memory_context else 0
    if mem_hit_count:
        log.debug("[gaians/%s] Injected %d memory items into system prompt", slug, mem_hit_count)

    # ─ Step 3: stream tokens via SSE ───────────────────────────────────────────
    async def _event_stream():
        full_text: list[str] = []
        try:
            async for token in llm_stream(
                prompt=result.user_message,
                system=system_prompt,
            ):
                full_text.append(token)
                payload = _json.dumps({"text": token}, ensure_ascii=False)
                yield f"event: token\ndata: {payload}\n\n"

        except RuntimeError as exc:
            log.error("[gaians/%s] LLM stream failed: %s", slug, exc)
            err_payload = _json.dumps({"error": str(exc)}, ensure_ascii=False)
            yield f"event: error\ndata: {err_payload}\n\n"
            return

        # Persist exchange count
        runtime.attachment.total_exchanges += 1
        runtime._persist()

        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        snap       = result.state_snapshot

        done_payload = _json.dumps({
            "epistemic_label": snap.get("epistemic_label", "confident"),
            "backend_used":    snap.get("backend", "ollama"),
            "bond_depth":      snap.get("bond_depth", 0.0),
            "canon_docs":      snap.get("canon_docs", 0),
            "inference_ms":    elapsed_ms,
            "mem_hits_used":   mem_hit_count,
        }, ensure_ascii=False)
        yield f"event: done\ndata: {done_payload}\n\n"

    return StreamingResponse(
        _event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── LEGACY: /api/gaian/chat (blocking JSON) ──────────────────────────────────

@router.post(
    "/gaian/chat",
    response_model=ChatResponse,
    summary="Send a message to a Gaian (blocking JSON — legacy)",
)
async def gaian_chat(req: ChatRequest) -> ChatResponse:
    runtime = _get_runtime(req.gaian_name, req.memory_dir)

    try:
        result = runtime.process(req.message)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": "GAIAN runtime error", "detail": str(exc)},
        )

    system_prompt = _inject_memory(result.system_prompt, req.memory_context)

    try:
        llm_result = await generate(
            prompt=result.user_message,
            system=system_prompt,
        )
    except RuntimeError as exc:
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

    runtime.attachment.total_exchanges += 1
    runtime._persist()

    return ChatResponse(
        reply=llm_result.text,
        gaian_name=req.gaian_name,
        provider=llm_result.provider,
        model=llm_result.model,
        latency_ms=llm_result.latency_ms,
        offline=llm_result.offline,
        state_snapshot=result.state_snapshot,
    )


# ── LEGACY: /api/gaian/chat/stream (old SSE format) ───────────────────────

@router.post(
    "/gaian/chat/stream",
    summary="Send a message to a Gaian — SSE stream (legacy)",
)
async def gaian_chat_stream(req: ChatRequest) -> StreamingResponse:
    runtime = _get_runtime(req.gaian_name, req.memory_dir)

    try:
        result = runtime.process(req.message)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={"error": "GAIAN runtime error", "detail": str(exc)},
        )

    system_prompt = _inject_memory(result.system_prompt, req.memory_context)

    async def _event_stream():
        try:
            async for token in llm_stream(
                prompt=result.user_message,
                system=system_prompt,
            ):
                yield f"data: {token}\n\n"
        except RuntimeError as exc:
            yield f"event: error\ndata: All providers failed: {exc}\n\n"
            yield "data: [DONE]\n\n"
            return

        runtime.attachment.total_exchanges += 1
        runtime._persist()

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


# ── Status ──────────────────────────────────────────────────────────────────────────────────

@router.get(
    "/gaian/status",
    summary="Gaian runtime + routing status (for dev console)",
)
async def gaian_status(gaian_name: str = "Luna") -> dict:
    routing = await routing_status()
    if gaian_name.lower().strip() in _runtimes:
        gaian_st = _runtimes[gaian_name.lower().strip()].get_status()
    else:
        gaian_st = {"note": f"Runtime for '{gaian_name}' not yet initialised. Send a chat message first."}
    return {"gaian": gaian_st, "routing": routing}
