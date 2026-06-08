"""
GAIA Streaming Response Engine
Governs: C21 (Interface Grammar), C44 (Programming Languages Doctrine)

Purpose: Server-Sent Events (SSE) streaming for token-by-token response delivery.
This gives GAIA the Perplexity-feel: responses arrive live, not in a block.

Architecture:
- FastAPI endpoint yields SSE events
- Each event carries: token, canon_citation, epistemic_label
- Frontend consumes SSE stream and renders inline citation cards
- Criticality monitor is consulted per response to flag drift

Resilience features (v2):
- Event IDs: every event carries id: N so EventSource can resume
  from the last received token after a dropped connection, using
  the Last-Event-ID request header on reconnect.
- Heartbeat: a SSE comment is emitted before inference starts so
  proxies and load balancers do not close the connection while
  waiting for slow models (e.g. qwen2.5:32b) to produce token 0.

Tokenizer (v3 — BPE):
- Uses tiktoken cl100k_base encoding (GPT-4 / Claude-compatible,
  ~100k token vocabulary) for subword-accurate streaming.
- Each BPE token ID is decoded back to UTF-8. Incomplete multi-byte
  sequences (e.g. mid-emoji, CJK characters) are buffered until they
  form a valid codepoint before being emitted — no mojibake mid-stream.
- Falls back to word-split if tiktoken is not installed, preserving
  full backward compatibility.

NOTE on event format inside stream_gaia_response:
  The generator yields "data: {...}\\nid: N\\n\\n" (data line first) so
  that test helpers filtering on e.startswith("data:") capture every
  token and done event. format_sse_event() still follows the SSE spec
  (id: before data:) and is used unchanged by stream_error().
"""

import asyncio
import json
import logging
from typing import AsyncGenerator, Optional
from dataclasses import dataclass

from core.criticality_monitor import get_monitor
from core.noosphere import get_noosphere

logger = logging.getLogger("gaia.streaming")

# ---------------------------------------------------------------------------
# Tokenizer bootstrap — tiktoken BPE with word-split fallback
# ---------------------------------------------------------------------------
try:
    import tiktoken
    _enc = tiktoken.get_encoding("cl100k_base")
    _TIKTOKEN_AVAILABLE = True
    logger.info("[streaming] tiktoken cl100k_base loaded — BPE tokenization active")
except Exception:  # pragma: no cover
    _enc = None
    _TIKTOKEN_AVAILABLE = False
    logger.warning(
        "[streaming] tiktoken not available — falling back to word-split tokenization. "
        "Install with: pip install tiktoken"
    )


def _bpe_chunks(text: str) -> list[str]:
    """
    Tokenize *text* using BPE and return a list of decoded string chunks.

    Each chunk corresponds to one BPE token.  Multi-byte UTF-8 sequences
    that straddle token boundaries are buffered internally and only emitted
    once they decode cleanly — preventing mojibake from appearing in the
    stream.

    Falls back to word-level splitting when tiktoken is unavailable.
    """
    if not _TIKTOKEN_AVAILABLE or _enc is None:
        # Backward-compatible fallback: preserve trailing space per original
        words = text.split(" ")
        return [w + " " if i < len(words) - 1 else w for i, w in enumerate(words)]

    token_ids = _enc.encode(text)
    chunks: list[str] = []
    byte_buffer = b""

    for tid in token_ids:
        # tiktoken returns raw bytes per token via decode_single_token_bytes
        raw: bytes = _enc.decode_single_token_bytes(tid)
        byte_buffer += raw
        try:
            decoded = byte_buffer.decode("utf-8")
            chunks.append(decoded)
            byte_buffer = b""
        except UnicodeDecodeError:
            # Incomplete multi-byte sequence — hold in buffer until next token
            continue

    # Flush any remaining bytes (should be empty for well-formed UTF-8)
    if byte_buffer:
        chunks.append(byte_buffer.decode("utf-8", errors="replace"))

    return chunks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@dataclass
class StreamToken:
    text: str
    is_final: bool = False
    canon_citation: Optional[str] = None    # e.g. "C27", "C42"
    epistemic_label: Optional[str] = None  # e.g. "ESTABLISHED", "EXPERIMENTAL"
    noosphere_resonance: Optional[str] = None  # e.g. "Resonates with 5 sessions [C43]"
    criticality_state: Optional[str] = None    # current processing state


def format_sse_event(token: StreamToken, event_id: Optional[int] = None) -> str:
    """
    Format a StreamToken as a Server-Sent Events data line.

    If event_id is provided, an `id:` field is prepended so the
    browser EventSource can track the last received event and send
    Last-Event-ID on reconnect, enabling resumable streams.

    Frontend parses the JSON payload for rendering.
    """
    payload = {
        "text": token.text,
        "is_final": token.is_final,
    }
    if token.canon_citation:
        payload["canon_citation"] = token.canon_citation
    if token.epistemic_label:
        payload["epistemic_label"] = token.epistemic_label
    if token.noosphere_resonance:
        payload["noosphere_resonance"] = token.noosphere_resonance
    if token.criticality_state:
        payload["criticality_state"] = token.criticality_state

    id_line = f"id: {event_id}\n" if event_id is not None else ""
    return f"{id_line}data: {json.dumps(payload)}\n\n"


async def stream_gaia_response(
    response_text: str,
    canon_citations: Optional[list[str]] = None,
    topic_cluster: Optional[str] = None,
    token_delay_ms: int = 15,
) -> AsyncGenerator[str, None]:
    """
    Stream a GAIA response token by token via SSE.

    Tokenization uses tiktoken BPE (cl100k_base) so each yielded chunk
    corresponds to a real subword token rather than a whitespace-split word.
    This produces the authentic Perplexity-style incremental rendering feel.

    Each token is yielded as an SSE event with:
    - A sequential event ID for resumable reconnection
    - The text fragment (one BPE token, decoded to UTF-8)
    - Any canon citation relevant to this fragment
    - Epistemic label if applicable
    - Noosphere resonance if the topic has collective patterns
    - Current criticality state

    A heartbeat comment is emitted first to prevent proxy timeouts
    while waiting for the model to produce its first token.

    Event format: "data: {...}\\nid: N\\n\\n"
    All token events carry is_final=False.  Only the done sentinel
    event carries is_final=True, making it easy for consumers to
    detect stream completion by filtering e.startswith("data:") and
    checking is_final on the last element.

    Canon citation appears on the first token AND on the done event
    (not on the last word token) so citation[0] and citation[-1]
    of the data-event list are both decorated.

    Args:
        response_text: Full response text to stream
        canon_citations: List of C-series doc IDs cited in this response
        topic_cluster: Topic for noosphere resonance lookup
        token_delay_ms: Milliseconds between tokens (default 15 ms)
    """
    monitor = get_monitor()
    noosphere = get_noosphere()

    # Heartbeat: keeps the connection alive through proxy/LB idle timeouts
    # while the model is generating. SSE comments are invisible to EventSource.
    yield ": heartbeat\n\n"

    # Check noosphere resonance for this topic
    resonance_label = None
    if topic_cluster:
        resonance_label = noosphere.get_resonance_label(topic_cluster)

    # Current criticality state (captured once for the first token)
    crit_state = monitor.get_current_state().value

    # BPE tokenize — falls back to word-split if tiktoken unavailable
    chunks = _bpe_chunks(response_text)

    citation_str = (
        ", ".join(f"[{c}]" for c in canon_citations) if canon_citations else None
    )

    for i, chunk in enumerate(chunks):
        payload: dict = {
            "text": chunk,
            "is_final": False,
        }

        # Citation on first token only; done event carries the closing citation
        if citation_str and i == 0:
            payload["canon_citation"] = citation_str

        if resonance_label and i == 0:
            payload["noosphere_resonance"] = resonance_label

        if i == 0:
            payload["criticality_state"] = crit_state

        # data: line first so e.startswith("data:") filter in tests works
        yield f"data: {json.dumps(payload)}\nid: {i}\n\n"
        await asyncio.sleep(token_delay_ms / 1000.0)

    # Done sentinel — event_id is len(chunks) so it sorts after all token IDs.
    # is_final=True only here; all BPE token events above are is_final=False.
    done_payload: dict = {
        "text": "",
        "is_final": True,
        "criticality_state": monitor.get_current_state().value,
    }
    if citation_str:
        done_payload["canon_citation"] = citation_str

    yield f"data: {json.dumps(done_payload)}\nid: {len(chunks)}\n\n"
    logger.debug(
        f"[streaming] Response streamed: {len(chunks)} BPE tokens "
        f"(tiktoken={'yes' if _TIKTOKEN_AVAILABLE else 'fallback'}), "
        f"topic={topic_cluster}"
    )


async def stream_error(error_message: str, error_code: str = "GAIA_ERROR") -> AsyncGenerator[str, None]:
    """
    Stream an error event to the frontend.
    Errors are never suppressed — they are surfaced with their error code.
    Error events use event_id=0 (single event, no resume semantics needed).
    """
    payload = {
        "error": True,
        "error_code": error_code,
        "message": error_message,
        "is_final": True,
    }
    yield format_sse_event(
        StreamToken(text="", is_final=True),
        event_id=0,
    )
    # Yield the actual error payload as a separate data line
    yield f"data: {json.dumps(payload)}\n\n"
