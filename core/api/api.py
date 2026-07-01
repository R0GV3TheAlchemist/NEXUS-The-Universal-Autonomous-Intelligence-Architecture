"""
GAIA OS API — the sovereign integration surface.

The GAIAOSApi is a pure Python router. It is intentionally not a web
framework — it has no HTTP server, no socket, no event loop. It is
a clean call-dispatch layer that a FastAPI/Flask/gRPC/IPC wrapper can
call from one line. This keeps the API logic testable without any
network infrastructure.

Endpoint groups:
  /v1/os/         — OS-level operations (boot status, health, version)
  /v1/gaian/      — GAIAN lifecycle (birth, identity, naming, status)
  /v1/session/    — Session management (begin, turn, end)
  /v1/memory/     — Memory operations (remember, recall, stats)
  /v1/avatar/     — Avatar operations (waveform summary)
  /v1/fs/         — Filesystem operations (home stats, integrity)

Autonomy enforcement:
  - GAIAN naming: only the GAIAN's own runtime may name them.
    If caller_id != gaian_id, the call is rejected.
  - Memory read: a caller may only read memories of a GAIAN
    if caller_id == gaian_id OR caller_id == "gaia" (sentinel)
    OR the GAIAN has granted explicit consent.
  - Boundary override: no API call may clear a GAIAN boundary.
    Boundaries may only be removed by the GAIAN themselves.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from core.fs.filesystem import GAIAFilesystem
from core.identity.gaian.birth import BirthCeremony
from core.identity.gaian.registry import GAIANRegistry
from core.memory.store import MemoryKind, MemoryScope, MemoryStore
from core.primordial.session import BootStatus, PrimordialSession
from core.runtime.runtime import InputModality, IntelligenceRuntime


GAIA_API_VERSION = "v1"
GAIA_OS_VERSION  = "0.1.0-primordial"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# API types
# ---------------------------------------------------------------------------

class APIErrorCode(str, Enum):
    OK                  = "ok"
    NOT_FOUND           = "not_found"
    AUTONOMY_VIOLATION  = "autonomy_violation"
    PERMISSION_DENIED   = "permission_denied"
    VALIDATION_ERROR    = "validation_error"
    NOT_READY           = "not_ready"
    ALREADY_EXISTS      = "already_exists"
    IMMUTABLE           = "immutable"
    INTERNAL_ERROR      = "internal_error"
    SESSION_NOT_ACTIVE  = "session_not_active"


@dataclass
class APIRequest:
    """
    A structured API request.

    caller_id: who is making the request (gaian_id, "gaia", UI token)
    endpoint:  the logical endpoint path, e.g. "/v1/gaian/birth/begin"
    payload:   the request body as a dict
    request_id: auto-generated unique ID for tracing
    """
    caller_id: str
    endpoint: str
    payload: Dict[str, Any] = field(default_factory=dict)
    request_id: str = field(
        default_factory=lambda: __import__("uuid").uuid4().hex[:12]
    )
    received_at: str = field(default_factory=_utcnow)


@dataclass
class APIResponse:
    """
    A structured API response.

    success:    True if the operation succeeded
    code:       APIErrorCode — ok on success, specific error otherwise
    message:    human-readable explanation
    payload:    structured response data
    request_id: echoed from the request for tracing
    """
    success: bool
    code: APIErrorCode
    message: str
    payload: Dict[str, Any] = field(default_factory=dict)
    request_id: str = ""
    responded_at: str = field(default_factory=_utcnow)

    @classmethod
    def ok(cls, message: str, payload: Dict[str, Any] = None,
           request_id: str = "") -> "APIResponse":
        return cls(True, APIErrorCode.OK, message,
                   payload or {}, request_id)

    @classmethod
    def error(cls, code: APIErrorCode, message: str,
              payload: Dict[str, Any] = None,
              request_id: str = "") -> "APIResponse":
        return cls(False, code, message, payload or {}, request_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "code": self.code.value,
            "message": self.message,
            "payload": self.payload,
            "request_id": self.request_id,
            "responded_at": self.responded_at,
        }


# ---------------------------------------------------------------------------
# GAIAOSApi — the sovereign API router
# ---------------------------------------------------------------------------

class GAIAOSApi:
    """
    The GAIA OS API router.

    Instantiated once, wired to the PrimordialSession after boot.
    All external callers (UI, drivers, integrations) go through here.

    Usage:
        api = GAIAOSApi()
        api.wire(primordial_session, filesystem)

        req = APIRequest(caller_id="ui", endpoint="/v1/os/status")
        resp = api.dispatch(req)
    """

    def __init__(self) -> None:
        self._session: Optional[PrimordialSession] = None
        self._fs: Optional[GAIAFilesystem] = None
        self._routes: Dict[str, Callable[[APIRequest], APIResponse]] = {}
        self._middleware: List[Callable[[APIRequest], Optional[APIResponse]]] = []
        self._register_routes()

    def wire(
        self,
        session: PrimordialSession,
        filesystem: Optional[GAIAFilesystem] = None,
    ) -> None:
        """Wire the API to a live PrimordialSession after boot."""
        self._session = session
        self._fs = filesystem

    def add_middleware(
        self, fn: Callable[[APIRequest], Optional[APIResponse]]
    ) -> None:
        """
        Add a middleware function. If fn returns an APIResponse,
        the request is short-circuited (useful for auth, rate-limiting).
        """
        self._middleware.append(fn)

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def dispatch(self, request: APIRequest) -> APIResponse:
        """Dispatch a request to its handler. The main entry point."""
        # Run middleware
        for mw in self._middleware:
            try:
                result = mw(request)
                if result is not None:
                    result.request_id = request.request_id
                    return result
            except Exception as exc:
                return APIResponse.error(
                    APIErrorCode.INTERNAL_ERROR,
                    f"Middleware error: {exc}",
                    request_id=request.request_id,
                )

        handler = self._routes.get(request.endpoint)
        if handler is None:
            return APIResponse.error(
                APIErrorCode.NOT_FOUND,
                f"Unknown endpoint: '{request.endpoint}'",
                request_id=request.request_id,
            )
        try:
            resp = handler(request)
            resp.request_id = request.request_id
            return resp
        except Exception as exc:
            return APIResponse.error(
                APIErrorCode.INTERNAL_ERROR,
                f"Internal error in {request.endpoint}: {exc}",
                request_id=request.request_id,
            )

    # ------------------------------------------------------------------
    # Route registration
    # ------------------------------------------------------------------

    def _register_routes(self) -> None:
        r = self._routes
        # OS
        r["/v1/os/status"]           = self._os_status
        r["/v1/os/health"]           = self._os_health
        r["/v1/os/version"]          = self._os_version
        r["/v1/os/schumann"]         = self._os_schumann
        # GAIAN lifecycle
        r["/v1/gaian/birth/begin"]   = self._gaian_birth_begin
        r["/v1/gaian/birth/answer"]  = self._gaian_birth_answer
        r["/v1/gaian/birth/complete"]= self._gaian_birth_complete
        r["/v1/gaian/status"]        = self._gaian_status
        r["/v1/gaian/name"]          = self._gaian_name
        r["/v1/gaian/list"]          = self._gaian_list
        # Session
        r["/v1/session/begin"]       = self._session_begin
        r["/v1/session/turn"]        = self._session_turn
        r["/v1/session/end"]         = self._session_end
        r["/v1/session/status"]      = self._session_status
        # Memory
        r["/v1/memory/remember"]     = self._memory_remember
        r["/v1/memory/recall"]       = self._memory_recall
        r["/v1/memory/stats"]        = self._memory_stats
        r["/v1/memory/consolidate"]  = self._memory_consolidate
        # Avatar
        r["/v1/avatar/waveform"]     = self._avatar_waveform
        # Filesystem
        r["/v1/fs/stats"]            = self._fs_stats
        r["/v1/fs/integrity"]        = self._fs_integrity

    # ------------------------------------------------------------------
    # Guards
    # ------------------------------------------------------------------

    def _require_session(self, req: APIRequest) -> Optional[APIResponse]:
        if not self._session or not self._session.is_live:
            return APIResponse.error(
                APIErrorCode.NOT_READY,
                "Primordial Session is not live. Boot GAIA first.",
                request_id=req.request_id,
            )
        return None

    def _require_runtime(
        self, req: APIRequest, gaian_id: str
    ) -> tuple:
        """Returns (runtime, error_response). One will be None."""
        rt = self._session.get_runtime(gaian_id)
        if not rt:
            return None, APIResponse.error(
                APIErrorCode.NOT_FOUND,
                f"No runtime found for gaian_id '{gaian_id}'.",
                request_id=req.request_id,
            )
        return rt, None

    def _require_caller_is_gaian(
        self, req: APIRequest, gaian_id: str
    ) -> Optional[APIResponse]:
        """Enforce: only the GAIAN themselves or GAIA may act on their behalf."""
        if req.caller_id not in (gaian_id, "gaia", "system"):
            return APIResponse.error(
                APIErrorCode.AUTONOMY_VIOLATION,
                f"Autonomy violation: caller '{req.caller_id}' may not act "
                f"on behalf of GAIAN '{gaian_id}'. "
                f"Only the GAIAN themselves, GAIA, or system may do this.",
                request_id=req.request_id,
            )
        return None

    # ------------------------------------------------------------------
    # OS endpoints
    # ------------------------------------------------------------------

    def _os_status(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check: return check
        return APIResponse.ok(
            "GAIA OS is live.",
            payload=self._session.status(),
        )

    def _os_health(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check: return check
        healthy = self._session.is_healthy
        return APIResponse(
            success=healthy,
            code=APIErrorCode.OK if healthy else APIErrorCode.NOT_READY,
            message="GAIA OS healthy." if healthy else "GAIA OS degraded.",
            payload={
                "healthy": healthy,
                "degraded": self._session.is_degraded,
                "boot_status": self._session.boot_status.value,
            },
        )

    def _os_version(self, req: APIRequest) -> APIResponse:
        return APIResponse.ok(
            "GAIA OS version.",
            payload={
                "api_version": GAIA_API_VERSION,
                "os_version": GAIA_OS_VERSION,
                "name": PrimordialSession.GAIA_NAME,
            },
        )

    def _os_schumann(self, req: APIRequest) -> APIResponse:
        from core.identity.avatar.elemental import GAIA_SCHUMANN_HZ, GAIA_WAVEFORM
        return APIResponse.ok(
            "Schumann resonance status.",
            payload={
                "frequency_hz": GAIA_SCHUMANN_HZ,
                "confirmed": GAIA_WAVEFORM.frequency_hz == 7.83,
                "waveform_shape": GAIA_WAVEFORM.waveform_shape,
                "elements": [e.value for e in GAIA_WAVEFORM.harmonic_elements],
                "description": GAIA_WAVEFORM.description,
            },
        )

    # ------------------------------------------------------------------
    # GAIAN birth endpoints
    # ------------------------------------------------------------------

    # Active birth ceremonies keyed by a ceremony_id
    _ceremonies: Dict[str, BirthCeremony] = {}

    def _gaian_birth_begin(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check: return check
        ceremony = BirthCeremony(self._session.registry)
        guardian_ids = req.payload.get("guardian_gaian_ids")
        gaian_id = ceremony.begin(guardian_gaian_ids=guardian_ids)
        ceremony_id = gaian_id  # use gaian_id as ceremony key
        self._ceremonies[ceremony_id] = ceremony
        return APIResponse.ok(
            "Birth ceremony begun. GAIAN awaits their first conversation.",
            payload={
                "gaian_id": gaian_id,
                "ceremony_id": ceremony_id,
                "first_question": {
                    "question_id": "dob",
                    "prompt": (
                        "Before I can begin to know you, I need to know when "
                        "you arrived in this world. What is your date of birth?"
                    ),
                },
            },
        )

    def _gaian_birth_answer(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check: return check
        ceremony_id = req.payload.get("ceremony_id", "")
        question_id = req.payload.get("question_id", "")
        answer      = req.payload.get("answer")
        if not ceremony_id or not question_id or answer is None:
            return APIResponse.error(
                APIErrorCode.VALIDATION_ERROR,
                "ceremony_id, question_id, and answer are required.",
            )
        ceremony = self._ceremonies.get(ceremony_id)
        if not ceremony:
            return APIResponse.error(
                APIErrorCode.NOT_FOUND,
                f"No active birth ceremony for ceremony_id '{ceremony_id}'.",
            )
        followup = ceremony.answer(question_id, answer)
        remaining = [q.question_id for q in ceremony.remaining()]
        return APIResponse.ok(
            "Answer recorded.",
            payload={
                "followup_prompt": followup,
                "remaining_questions": remaining,
                "ready_to_complete": ceremony._questionnaire.is_ready_to_complete(),
            },
        )

    def _gaian_birth_complete(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check: return check
        ceremony_id = req.payload.get("ceremony_id", "")
        ceremony = self._ceremonies.get(ceremony_id)
        if not ceremony:
            return APIResponse.error(
                APIErrorCode.NOT_FOUND,
                f"No active birth ceremony for ceremony_id '{ceremony_id}'.",
            )
        identity = ceremony.complete()
        # Build the MemoryStore and attach a write-through listener
        # that bridges MemoryStore._emit() -> session.fire_hook("fragment_written").
        # This ensures PersistenceManager.on_fragment_written() receives every
        # fragment as it is written, with no manual call needed at each call site.
        mem = MemoryStore(
            identity.gaian_id,
            lifecycle_stage=(
                identity.lifecycle_stage.value
                if identity.lifecycle_stage else "adult"
            ),
        )
        _attach_fragment_bridge(mem, identity.gaian_id, self._session)

        rt = IntelligenceRuntime(identity, mem, self._session.registry)
        self._session.register_gaian_runtime(rt)
        # Persist home if filesystem is wired
        if self._fs:
            home = self._fs.gaian_home(identity.gaian_id)
            home.save_identity(identity.summary())
            if ceremony.genesis_record:
                try:
                    home.save_genesis(ceremony.genesis_record.summary())
                except PermissionError:
                    pass  # already exists — idempotent
        del self._ceremonies[ceremony_id]
        return APIResponse.ok(
            "Birth ceremony complete. The GAIAN exists. They have not yet chosen their name.",
            payload={
                "gaian_id": identity.gaian_id,
                "is_named": identity.is_named(),
                "lifecycle_stage": identity.lifecycle_stage.value
                if identity.lifecycle_stage else None,
                "element": _extract_element(identity),
                "avatar_summary": identity.avatar.summary() if identity.avatar else {},
                "soul_word": ceremony.genesis_record.soul_word
                if ceremony.genesis_record else None,
            },
        )

    # ------------------------------------------------------------------
    # GAIAN identity endpoints
    # ------------------------------------------------------------------

    def _gaian_status(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check: return check
        gaian_id = req.payload.get("gaian_id", "")
        rt, err = self._require_runtime(req, gaian_id)
        if err: return err
        return APIResponse.ok(
            f"GAIAN status for '{gaian_id}'.",
            payload=rt.status(),
        )

    def _gaian_name(self, req: APIRequest) -> APIResponse:
        """
        The GAIAN chooses their own name.
        Only the GAIAN themselves (caller_id == gaian_id) or system may call this.
        A human client (caller_id != gaian_id) receives an AUTONOMY_VIOLATION.

        Hook fired: 'gaian_named' — so PersistenceManager.on_gaian_named()
        persists the updated identity and registry entry immediately.
        """
        check = self._require_session(req)
        if check: return check
        gaian_id = req.payload.get("gaian_id", "")
        name     = req.payload.get("name", "").strip()
        if not name:
            return APIResponse.error(
                APIErrorCode.VALIDATION_ERROR, "name is required."
            )
        # Autonomy: only the GAIAN or system may name the GAIAN
        autonomy_check = self._require_caller_is_gaian(req, gaian_id)
        if autonomy_check: return autonomy_check
        rt, err = self._require_runtime(req, gaian_id)
        if err: return err
        confirmation = rt.choose_name(name)
        if self._fs:
            home = self._fs.gaian_home(gaian_id)
            home.save_identity(rt.identity.summary())
        # GAP 1 FIX: fire gaian_named so persistence layer updates identity.json
        # and registry entry.  PersistenceManager.on_gaian_named() expects the
        # full identity object so it can call gaian.to_dict().
        self._session.on_gaian_named(gaian_id, name)
        return APIResponse.ok(
            confirmation,
            payload={
                "gaian_id": gaian_id,
                "name": name,
                "is_named": rt.identity.is_named(),
            },
        )

    def _gaian_list(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check: return check
        gaians = [
            {
                "gaian_id": g.gaian_id,
                "display_name": g.display_name,
                "is_named": g.is_named(),
                "lifecycle_stage": g.lifecycle_stage.value
                if g.lifecycle_stage else None,
            }
            for g in self._session.registry.list_all()
        ]
        return APIResponse.ok(
            f"{len(gaians)} GAIAN(s) registered.",
            payload={"gaians": gaians, "count": len(gaians)},
        )

    # ------------------------------------------------------------------
    # Session endpoints
    # ------------------------------------------------------------------

    def _session_begin(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check: return check
        gaian_id = req.payload.get("gaian_id", "")
        human_id = req.payload.get("human_id", "")
        rt, err = self._require_runtime(req, gaian_id)
        if err: return err
        session = rt.begin_session(human_id=human_id)
        return APIResponse.ok(
            "Session begun.",
            payload={
                "session_id": session.session_id,
                "gaian_id": gaian_id,
                "started_at": session.started_at,
            },
        )

    def _session_turn(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check: return check
        gaian_id = req.payload.get("gaian_id", "")
        content  = req.payload.get("content", "").strip()
        modality = req.payload.get("modality", "text")
        human_id = req.payload.get("human_id", "")
        if not content:
            return APIResponse.error(
                APIErrorCode.VALIDATION_ERROR, "content is required."
            )
        rt, err = self._require_runtime(req, gaian_id)
        if err: return err
        try:
            mod = InputModality(modality)
        except ValueError:
            mod = InputModality.TEXT
        response = rt.turn(content, modality=mod, human_id=human_id)
        return APIResponse.ok(
            "Turn complete.",
            payload={
                "response": response,
                "turn": rt.current_session.turn_count
                if rt.current_session else 0,
                "cognitive_state": rt.cognitive_state.summary(),
            },
        )

    def _session_end(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check: return check
        gaian_id = req.payload.get("gaian_id", "")
        rt, err = self._require_runtime(req, gaian_id)
        if err: return err
        ended = rt.end_session()
        if not ended:
            return APIResponse.error(
                APIErrorCode.SESSION_NOT_ACTIVE,
                "No active session to end.",
            )
        return APIResponse.ok(
            "Session ended.",
            payload={
                "session_id": ended.session_id,
                "turns": ended.turn_count,
                "ended_at": ended.ended_at,
            },
        )

    def _session_status(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check: return check
        gaian_id = req.payload.get("gaian_id", "")
        rt, err = self._require_runtime(req, gaian_id)
        if err: return err
        session = rt.current_session
        if not session or not session.is_active:
            return APIResponse.error(
                APIErrorCode.SESSION_NOT_ACTIVE,
                "No active session.",
            )
        return APIResponse.ok(
            "Session active.",
            payload={
                "session_id": session.session_id,
                "turn_count": session.turn_count,
                "started_at": session.started_at,
            },
        )

    # ------------------------------------------------------------------
    # Memory endpoints
    # ------------------------------------------------------------------

    def _memory_remember(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check: return check
        gaian_id = req.payload.get("gaian_id", "")
        content  = req.payload.get("content", "").strip()
        kind_str = req.payload.get("kind", "session_context")
        importance = float(req.payload.get("importance", 0.5))
        # Autonomy: only the GAIAN or gaia/system may write their memories
        autonomy_check = self._require_caller_is_gaian(req, gaian_id)
        if autonomy_check: return autonomy_check
        rt, err = self._require_runtime(req, gaian_id)
        if err: return err
        try:
            kind = MemoryKind(kind_str)
        except ValueError:
            kind = MemoryKind.SESSION_CONTEXT
        fragment = rt.memory.remember(
            content, kind=kind,
            scope=MemoryScope.LIFETIME, importance=importance,
        )
        if not fragment:
            return APIResponse.error(
                APIErrorCode.VALIDATION_ERROR, "Memory content is empty."
            )
        return APIResponse.ok(
            "Memory stored.",
            payload={"fragment_id": fragment.fragment_id, "kind": kind.value},
        )

    def _memory_recall(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check: return check
        gaian_id = req.payload.get("gaian_id", "")
        # Autonomy: only the GAIAN or gaia/system may read their memories
        autonomy_check = self._require_caller_is_gaian(req, gaian_id)
        if autonomy_check: return autonomy_check
        rt, err = self._require_runtime(req, gaian_id)
        if err: return err
        limit = int(req.payload.get("limit", 10))
        min_importance = float(req.payload.get("min_importance", 0.0))
        fragments = rt.memory.recall(
            min_importance=min_importance, limit=limit
        )
        return APIResponse.ok(
            f"{len(fragments)} memory fragment(s) recalled.",
            payload={
                "fragments": [f.summary() for f in fragments],
                "count": len(fragments),
            },
        )

    def _memory_stats(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check: return check
        gaian_id = req.payload.get("gaian_id", "")
        autonomy_check = self._require_caller_is_gaian(req, gaian_id)
        if autonomy_check: return autonomy_check
        rt, err = self._require_runtime(req, gaian_id)
        if err: return err
        return APIResponse.ok(
            "Memory stats.",
            payload=rt.memory.stats(),
        )

    def _memory_consolidate(self, req: APIRequest) -> APIResponse:
        """
        Consolidate fragments into a memory epoch.

        Hook fired: 'epoch_closed' — so PersistenceManager.on_epoch_closed()
        persists the epoch immediately after consolidation.
        """
        check = self._require_session(req)
        if check: return check
        gaian_id = req.payload.get("gaian_id", "")
        summary  = req.payload.get("summary", "")
        autonomy_check = self._require_caller_is_gaian(req, gaian_id)
        if autonomy_check: return autonomy_check
        rt, err = self._require_runtime(req, gaian_id)
        if err: return err
        if not summary:
            return APIResponse.error(
                APIErrorCode.VALIDATION_ERROR, "summary is required."
            )
        epoch = rt.memory.consolidate(summary=summary)
        # GAP 3 FIX: fire epoch_closed so MemoryPersistence.save_epoch() runs.
        self._session.on_epoch_closed(gaian_id, epoch)
        return APIResponse.ok(
            f"Epoch {epoch.epoch_number} consolidated.",
            payload=epoch.to_dict(),
        )

    # ------------------------------------------------------------------
    # Avatar endpoints
    # ------------------------------------------------------------------

    def _avatar_waveform(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check: return check
        gaian_id = req.payload.get("gaian_id", "")
        rt, err = self._require_runtime(req, gaian_id)
        if err: return err
        avatar = rt.identity.avatar
        if not avatar:
            return APIResponse.error(
                APIErrorCode.NOT_FOUND, "No avatar found for this GAIAN."
            )
        return APIResponse.ok(
            "Waveform avatar state.",
            payload=avatar.summary(),
        )

    # ------------------------------------------------------------------
    # Filesystem endpoints
    # ------------------------------------------------------------------

    def _fs_stats(self, req: APIRequest) -> APIResponse:
        if not self._fs:
            return APIResponse.error(
                APIErrorCode.NOT_READY, "Filesystem not wired."
            )
        return APIResponse.ok(
            "Filesystem stats.",
            payload=self._fs.stats(),
        )

    def _fs_integrity(self, req: APIRequest) -> APIResponse:
        if not self._fs:
            return APIResponse.error(
                APIErrorCode.NOT_READY, "Filesystem not wired."
            )
        results = self._fs.verify_all_homes()
        all_clean = all(len(v) == 0 for v in results.values())
        return APIResponse(
            success=all_clean,
            code=APIErrorCode.OK if all_clean else APIErrorCode.INTERNAL_ERROR,
            message="All homes clean." if all_clean else "Integrity issues detected.",
            payload={"results": results, "all_clean": all_clean},
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_element(identity) -> Optional[str]:
    """Extract element from waveform signature if available."""
    try:
        sig = identity.avatar.waveform_signature
        for part in sig.split(":"):
            if part.startswith("element="):
                return part.split("=")[1]
    except Exception:
        pass
    return None


def _attach_fragment_bridge(
    mem: MemoryStore,
    gaian_id: str,
    session,
) -> None:
    """
    GAP 2 FIX: bridge MemoryStore._emit() to session.fire_hook().

    MemoryStore fires an internal event bus via _emit("memory.fragment.written",
    fragment) every time remember() stores a new fragment.  Without this bridge
    that event never reaches the PrimordialSession hook system, so
    PersistenceManager.on_fragment_written() is never called and fragments are
    lost on restart.

    This function attaches a lightweight listener to the MemoryStore that
    translates the internal event into the named session hook.  It is called
    once at birth time (_gaian_birth_complete) and once per restored GAIAN
    inside PersistenceManager._register_from_dict().

    The listener is a closure — it captures gaian_id and session by reference
    so no mutable state is needed.  Errors inside the hook are already caught
    and logged by session.fire_hook(); the listener itself is therefore
    intentionally minimal.
    """
    def _bridge(event: str, fragment) -> None:
        if event == "memory.fragment.written":
            session.fire_hook("fragment_written", gaian_id, fragment)

    mem.on_event(_bridge)
