"""
core/routers/chat.py

Conversation, query-stream, session, and GAIAN state read endpoints:
  GET  /memory/list
  POST /session/{session_id}/gaian
  POST /gaians/{slug}/chat           (SSE stream)
  POST /query/stream                 (SSE stream)
  GET  /gaians/{slug}/resonance
  GET  /gaians/{slug}/soul-mirror
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from core.auth import TokenPayload, require_auth
from core.codex_stage_engine import NoosphericHealthSignals
from core.gaian import GaianMemory, add_exchange, get_conversation_context, load_gaian
from core.inference_router import InferenceRequest, InferenceResponse
from core.logger import GAIAEvent, get_logger, log_event
from core.infra.memory_bridge import recall_for_prompt, store_turn  # unified memory layer
from core.rate_limiter import rate_limit
from core.server_models import ChatRequest, QueryRequest, SetGaianRequest
from core.server_state import _get_runtime, _inference_router, canon
from core.session_memory import get_or_create_session, get_session
from core.web_search import search_web_async

logger = get_logger(__name__)
router = APIRouter()


@router.get("/memory/list")
async def memory_list(session_id: Optional[str] = None):
    if not session_id:
        return {"memories": [], "count": 0}
    session = get_session(session_id)
    if not session:
        return {"memories": [], "count": 0}
    memories = [
        {"query": t.query, "timestamp": t.timestamp, "source_count": t.source_count}
        for t in session.turns
    ]
    return {"memories": memories, "count": len(memories)}


@router.post("/session/{session_id}/gaian")
async def set_session_gaian(
    session_id: str,
    req: SetGaianRequest,
    user: TokenPayload = Depends(require_auth),
):
    gaian = load_gaian(req.gaian_slug)
    if not gaian:
        raise HTTPException(status_code=404, detail=f"GAIAN '{req.gaian_slug}' not found")
    session = get_or_create_session(session_id)
    session.active_gaian_slug = req.gaian_slug
    return {"status": "ok", "gaian": gaian.name, "session_id": session_id, "user_id": user.user_id}


@router.post("/gaians/{slug}/chat")
async def gaian_chat(
    slug: str,
    req: ChatRequest,
    user: TokenPayload = Depends(require_auth),
    _rl=Depends(rate_limit(max_requests=30, window_seconds=60, scope="chat")),
):
    gaian = load_gaian(slug)
    if not gaian:
        raise HTTPException(status_code=404, detail=f"GAIAN '{slug}' not found")

    session_id = req.session_id or str(uuid.uuid4())
    session = get_or_create_session(session_id)

    async def event_stream():
        full_answer = ""
        t0 = time.perf_counter()
        try:
            rt = _get_runtime(slug, gaian)

            noosphere: Optional[NoosphericHealthSignals] = None
            if req.schumann_hz > 10.0:
                noosphere = NoosphericHealthSignals(schumann_boost=0.05)
            elif req.schumann_hz < 6.0:
                noosphere = NoosphericHealthSignals(schumann_boost=-0.05)

            result = rt.process(req.message, noosphere=noosphere)
            log_event(
                GAIAEvent.ENGINE_CHAIN,
                message=f"Engine chain: {slug} exchange={rt.attachment.total_exchanges}",
                gaian=slug,
                user_id=user.user_id,
                bond_depth=round(rt.attachment.bond_depth, 2),
            )

            yield f"event: engine_state\ndata: {json.dumps(result.state_snapshot)}\n\n"
            await asyncio.sleep(0.01)

            if result.soul_mirror.individuation_nudge:
                soul_mirror_data = {
                    'nudge':   result.soul_mirror.individuation_nudge,
                    'signal':  result.soul_mirror.shadow_signal.value,
                    'carrier': result.soul_mirror.projection_carrier.value,
                }
                yield f"event: soul_mirror\ndata: {json.dumps(soul_mirror_data)}\n\n"
                await asyncio.sleep(0.01)

            yield f"event: resonance_field\ndata: {json.dumps(result.resonance_field.summary())}\n\n"
            await asyncio.sleep(0.01)

            web_sources = []
            if req.enable_web_search:
                try:
                    web_results = await search_web_async(req.message, max_results=4)
                    web_sources = [
                        wr.to_dict() if hasattr(wr, "to_dict") else dict(wr)
                        for wr in web_results
                    ]
                except Exception as e:
                    logger.warning(f"Web search error in chat: {e}")

            # --- Unified memory recall via MemoryBridge (C17) ---
            # Routes through GAIANRuntime's MemoryStore (SQLite + sqlite-vec).
            # Falls back to ChromaDB if runtime not yet registered.
            # NOTE: rt.process() above already recalled memories internally and
            # baked them into result.system_prompt. This recall populates
            # visible_memories for the InferenceRouter's prompt block so the
            # router also sees recent episodic context in its own layer.
            recalled_memories = recall_for_prompt(
                query=req.message,
                gaian_slug=slug,
                top_k=5,
            )

            effective_prompt = result.system_prompt
            if result.soul_mirror.individuation_nudge:
                effective_prompt += (
                    "\n\n[SOUL MIRROR NUDGE AVAILABLE \u2014 use naturally if it fits]\n"
                    + result.soul_mirror.individuation_nudge
                )

            # Merge recalled memories with existing visible_memories
            existing_visible = [
                m["text"] for m in rt._memory.get("visible_memories", [])
                if isinstance(m, dict)
            ]
            all_visible = recalled_memories + existing_visible

            inference_req = InferenceRequest(
                query=req.message,
                gaian_slug=slug,
                gaian_system_prompt=effective_prompt,
                long_term_memories=gaian.long_term_memories or [],
                visible_memories=all_visible,
                conversation_history=get_conversation_context(gaian),
                conversation_context=session.get_context_summary() if session.turns else None,
                sources=web_sources,
                enrich_canon=True,
                canon_max_results=2,
                enrich_criticality=True,
                enrich_noosphere=True,
                schumann_hz=req.schumann_hz,
            )
            inference_meta = InferenceResponse(session_id=session_id, gaian_slug=slug)

            async for chunk in _inference_router.stream(inference_req, inference_meta):
                full_answer += chunk
                yield f"event: token\ndata: {json.dumps({'text': chunk})}\n\n"

            session.add_turn(req.message, full_answer, len(web_sources))
            if full_answer:
                add_exchange(gaian, req.message, full_answer)
                # Persist this turn through the unified MemoryBridge (C17)
                store_turn(
                    user_message=req.message,
                    gaian_response=full_answer,
                    gaian_slug=slug,
                    session_id=session_id,
                )

            duration_ms = round((time.perf_counter() - t0) * 1000, 1)
            log_event(
                GAIAEvent.TURN_COMPLETE,
                message=f"Turn complete: {slug}",
                gaian=slug,
                user_id=user.user_id,
                duration_ms=duration_ms,
                exchange=rt.attachment.total_exchanges,
                bond_depth=round(rt.attachment.bond_depth, 2),
            )

            done_data = {
                'session_id':          session_id,
                'gaian':               gaian.name,
                'gaian_slug':          slug,
                'user_id':             user.user_id,
                'exchange':            rt.attachment.total_exchanges,
                'bond_depth':          round(rt.attachment.bond_depth, 2),
                'individuation_phase': rt.soul_mirror_state.individuation_phase.value,
                'resonance_hz':        result.resonance_field.solfeggio.hz.value,
                'schumann_aligned':    result.resonance_field.schumann_aligned,
                'noosphere_health':    round(rt.codex_stage_state.noosphere_health, 4),
                'epistemic_label':     inference_meta.epistemic_label.value,
                'backend_used':        inference_meta.backend_used.value,
                'canon_docs':          inference_meta.canon_docs_injected,
                'noosphere_resonance': inference_meta.noosphere_resonance,
                'criticality_state':   inference_meta.criticality_state,
                'inference_ms':        inference_meta.duration_ms,
                'recalled_memories':   len(recalled_memories),
                'timestamp':           time.time(),
            }
            yield f"event: done\ndata: {json.dumps(done_data)}\n\n"

        except Exception as e:
            logger.error(
                f"Chat stream error [{slug}]: {e}",
                exc_info=True,
                extra={"event": GAIAEvent.TURN_ERROR.value, "gaian": slug},
            )
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/query/stream")
async def query_stream(
    req: QueryRequest,
    user: TokenPayload = Depends(require_auth),
    _rl=Depends(rate_limit(max_requests=20, window_seconds=60, scope="query")),
):
    session_id = req.session_id or str(uuid.uuid4())
    session = get_or_create_session(session_id)
    gaian_slug = req.gaian_slug or session.active_gaian_slug or "gaia"
    gaian: Optional[GaianMemory] = load_gaian(gaian_slug)
    if gaian is None:
        gaian = load_gaian("gaia")
        if gaian:
            gaian_slug = gaian.slug

    async def event_stream():
        full_answer = ""
        sources: list[dict] = []
        canon_results: list[dict] = []
        t0 = time.perf_counter()
        try:
            canon_results = canon.search(req.query, max_results=3)
            log_event(
                GAIAEvent.CANON_SEARCH,
                message=f"Canon search: {len(canon_results)} results",
                gaian=gaian_slug,
                user_id=user.user_id,
                results=len(canon_results),
            )

            for result in canon_results:
                src = {
                    "tier": "T1",
                    "title": result.get("title", ""),
                    "doc_id": result.get("doc_id", ""),
                    "excerpt": result.get("excerpt", ""),
                }
                sources.append(src)
                yield f"event: citation\ndata: {json.dumps(result)}\n\n"
                await asyncio.sleep(0.01)

            if req.enable_web_search:
                try:
                    web_results = await search_web_async(req.query, max_results=5)
                    for wr in web_results:
                        src = wr.to_dict() if hasattr(wr, "to_dict") else dict(wr)
                        src["tier"] = src.get("source_tier", "T4")
                        sources.append(src)
                        yield f"event: web_result\ndata: {json.dumps(src)}\n\n"
                        await asyncio.sleep(0.01)
                except Exception as e:
                    logger.warning(f"Web search failed: {e}")

            runtime_system_prompt = None
            conversation_history: Optional[list] = None
            long_term_memories: list = []
            visible_memories: list = []

            if gaian:
                rt = _get_runtime(gaian_slug, gaian)
                rt.canon_text = (
                    "\n\n".join(
                        "[{title}]\n{excerpt}".format(
                            title=r.get("title", ""), excerpt=r.get("excerpt", "")
                        )
                        for r in canon_results[:2]
                    )
                ) if canon_results else None
                result = rt.process(req.query)
                runtime_system_prompt = result.system_prompt
                yield f"event: engine_state\ndata: {json.dumps(result.state_snapshot)}\n\n"
                await asyncio.sleep(0.01)
                conversation_history = get_conversation_context(gaian)
                long_term_memories = gaian.long_term_memories or []
                # Unified memory recall via MemoryBridge (C17)
                recalled = recall_for_prompt(req.query, gaian_slug=gaian_slug, top_k=5)
                visible_memories = recalled + [
                    m["text"] for m in rt._memory.get("visible_memories", [])
                    if isinstance(m, dict)
                ]

            inference_req = InferenceRequest(
                query=req.query,
                gaian_slug=gaian_slug,
                gaian_system_prompt=runtime_system_prompt,
                long_term_memories=long_term_memories,
                visible_memories=visible_memories,
                conversation_history=conversation_history or [],
                conversation_context=session.get_context_summary() if session.turns else None,
                sources=sources,
                enrich_canon=True,
                canon_max_results=2,
                enrich_criticality=True,
                enrich_noosphere=True,
            )
            inference_meta = InferenceResponse(session_id=session_id, gaian_slug=gaian_slug)

            async for chunk in _inference_router.stream(inference_req, inference_meta):
                full_answer += chunk
                yield f"event: token\ndata: {json.dumps({'text': chunk})}\n\n"

            suggestions = _generate_suggestions(req.query, sources)
            yield f"event: suggestions\ndata: {json.dumps({'items': suggestions})}\n\n"

            session.add_turn(req.query, full_answer, len(sources))
            if gaian and full_answer:
                add_exchange(gaian, req.query, full_answer)

            duration_ms = round((time.perf_counter() - t0) * 1000, 1)
            log_event(
                GAIAEvent.TURN_COMPLETE,
                message="Query stream complete",
                gaian=gaian_slug,
                user_id=user.user_id,
                duration_ms=duration_ms,
                canon_refs=len(canon_results),
                web_results=len(sources) - len(canon_results),
            )

            done_data = {
                'canon_status':        canon.status,
                'docs_searched':       len(canon.list_documents()),
                'refs_found':          len(canon_results),
                'web_results':         len(sources) - len(canon_results),
                'session_id':          session_id,
                'user_id':             user.user_id,
                'gaian':               gaian.name if gaian else None,
                'gaian_slug':          gaian_slug,
                'epistemic_label':     inference_meta.epistemic_label.value,
                'backend_used':        inference_meta.backend_used.value,
                'canon_docs':          inference_meta.canon_docs_injected,
                'noosphere_resonance': inference_meta.noosphere_resonance,
                'criticality_state':   inference_meta.criticality_state,
                'inference_ms':        inference_meta.duration_ms,
                'timestamp':           time.time(),
            }
            yield f"event: done\ndata: {json.dumps(done_data)}\n\n"

        except Exception as e:
            logger.error(
                f"Stream error: {e}",
                exc_info=True,
                extra={"event": GAIAEvent.TURN_ERROR.value},
            )
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/gaians/{slug}/resonance")
async def get_gaian_resonance(slug: str):
    gaian = load_gaian(slug)
    if not gaian:
        raise HTTPException(status_code=404, detail=f"GAIAN '{slug}' not found")
    rt = _get_runtime(slug, gaian)
    rf = rt.resonance_field_state
    return {
        "slug": slug,
        "gaian": gaian.name,
        "dominant_hz": rf.dominant_hz,
        "dominant_chakra": rf.dominant_chakra,
        "schumann_alignment_count": rf.schumann_alignment_count,
        "schumann_first_timestamp": rf.schumann_first_timestamp,
        "phi_rolling_avg": round(rf.phi_rolling_avg, 4),
        "session_peak_hz": rf.session_peak_hz,
        "hz_history": rf.hz_history[-10:],
    }


@router.get("/gaians/{slug}/soul-mirror")
async def get_gaian_soul_mirror(slug: str):
    gaian = load_gaian(slug)
    if not gaian:
        raise HTTPException(status_code=404, detail=f"GAIAN '{slug}' not found")
    rt = _get_runtime(slug, gaian)
    sm = rt.soul_mirror_state
    return {
        "slug": slug,
        "gaian": gaian.name,
        "individuation_phase": sm.individuation_phase.value,
        "exchanges_in_phase": sm.exchanges_in_phase,
        "shadow_activations": sm.shadow_activations,
        "anima_animus_activations": sm.anima_animus_activations,
        "dependency_risk_events": sm.dependency_risk_events,
        "phase_entry_timestamp": sm.phase_entry_timestamp,
        "phase_history": sm.phase_history[-10:],
        "last_nudge_exchange": sm.last_nudge_exchange,
    }


def _generate_suggestions(query: str, sources: list[dict]) -> list[str]:
    suggestions = []
    for s in sources[:2]:
        title = s.get("title", "")
        if title:
            short = title.split(":")[-1].strip()[:40]
            if short:
                suggestions.append(f"Tell me more about {short}")
    suggestions.append("What does GAIA's canon say about this?")
    suggestions.append("What are the practical implications?")
    return suggestions[:3]
