"""
core/api/api.py
===============
GAIA OS API — the sovereign integration surface.

v2.1 — Audit ledger wired throughout. Every dispatch is recorded.
        auth middleware hook added (reads X-GAIA-Token / Bearer).
        New /v1/audit/* passthrough registered.

The GAIAOSApi is a pure Python router — no HTTP server, no socket,
no event loop. A FastAPI/Flask/gRPC/IPC wrapper calls dispatch() from
one line. This keeps the API logic testable without any network infra.

Endpoint groups:
  /v1/os/         — OS-level operations (boot status, health, version)
  /v1/gaian/      — GAIAN lifecycle (birth, identity, naming, status)
  /v1/session/    — Session management (begin, turn, end)
  /v1/memory/     — Memory operations (remember, recall, stats)
  /v1/avatar/     — Avatar operations (waveform summary)
  /v1/fs/         — Filesystem operations (home stats, integrity)
  /v1/audit/*     — Audit ledger passthrough (delegated to audit_router)

Autonomy enforcement:
  - GAIAN naming: only the GAIAN's own runtime may name them.
  - Memory read: caller_id == gaian_id OR "gaia" OR explicit consent.
  - Boundary override: no API call may clear a GAIAN boundary.

Audit enforcement:
  - Every dispatched request appends an ACTION_EXECUTED event.
  - Auth events are recorded via log_auth_event().
  - Document stamps recorded via log_document_stamped().
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

if TYPE_CHECKING:
    import fastapi

from core.audit.ledger import (
    ActionLedger,
    AuditEvent,
    EventType,
    get_default_ledger,
    log_auth_event,
    set_default_ledger,
)
from core.fs.filesystem import GAIAFilesystem
from core.identity.gaian.birth import BirthCeremony
from core.memory.store import MemoryKind, MemoryScope, MemoryStore
from core.primordial.session import PrimordialSession
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
    UNAUTHORIZED        = "unauthorized"


@dataclass
class APIRequest:
    caller_id:  str
    endpoint:   str
    payload:    Dict[str, Any] = field(default_factory=dict)
    request_id: str            = field(
        default_factory=lambda: __import__("uuid").uuid4().hex[:12]
    )
    received_at: str = field(default_factory=_utcnow)
    # v2.1: auth metadata forwarded from HTTP layer
    jti:         str = ""   # JWT token ID from X-GAIA-Token
    session_id:  str = ""   # logical session for audit grouping


@dataclass
class APIResponse:
    success:      bool
    code:         APIErrorCode
    message:      str
    payload:      Dict[str, Any] = field(default_factory=dict)
    request_id:   str            = ""
    responded_at: str            = field(default_factory=_utcnow)

    @classmethod
    def ok(
        cls,
        message: str,
        payload: Dict[str, Any] = None,
        request_id: str = "",
    ) -> "APIResponse":
        return cls(True, APIErrorCode.OK, message, payload or {}, request_id)

    @classmethod
    def error(
        cls,
        code: APIErrorCode,
        message: str,
        payload: Dict[str, Any] = None,
        request_id: str = "",
    ) -> "APIResponse":
        return cls(False, code, message, payload or {}, request_id)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success":      self.success,
            "code":         self.code.value,
            "message":      self.message,
            "payload":      self.payload,
            "request_id":   self.request_id,
            "responded_at": self.responded_at,
        }


# ---------------------------------------------------------------------------
# GAIAOSApi — the sovereign API router
# ---------------------------------------------------------------------------


class GAIAOSApi:
    def __init__(self, ledger: Optional[ActionLedger] = None) -> None:
        self._session:    Optional[PrimordialSession] = None
        self._fs:         Optional[GAIAFilesystem]    = None
        self._routes:     Dict[str, Callable[[APIRequest], APIResponse]] = {}
        self._middleware: List[Callable[[APIRequest], Optional[APIResponse]]] = []
        # Audit ledger — use provided or fall back to module default
        self._ledger: ActionLedger = ledger or get_default_ledger()
        self._register_routes()

    # ------------------------------------------------------------------
    # Wiring
    # ------------------------------------------------------------------

    def wire(
        self,
        session: PrimordialSession,
        filesystem: Optional[GAIAFilesystem] = None,
        ledger: Optional[ActionLedger] = None,
    ) -> None:
        self._session = session
        self._fs      = filesystem
        if ledger:
            self._ledger = ledger
            set_default_ledger(ledger)

    def add_middleware(
        self, fn: Callable[[APIRequest], Optional[APIResponse]]
    ) -> None:
        self._middleware.append(fn)

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def dispatch(self, request: APIRequest) -> APIResponse:
        # Run middleware chain
        for mw in self._middleware:
            try:
                result = mw(request)
                if result is not None:
                    result.request_id = request.request_id
                    self._audit(
                        request,
                        outcome="blocked",
                        justification=f"middleware: {result.message}",
                    )
                    return result
            except Exception as exc:
                resp = APIResponse.error(
                    APIErrorCode.INTERNAL_ERROR,
                    f"Middleware error: {exc}",
                    request_id=request.request_id,
                )
                self._audit(request, outcome="error")
                return resp

        handler = self._routes.get(request.endpoint)
        if handler is None:
            resp = APIResponse.error(
                APIErrorCode.NOT_FOUND,
                f"Unknown endpoint: '{request.endpoint}'",
                request_id=request.request_id,
            )
            self._audit(request, outcome="not_found")
            return resp

        try:
            resp = handler(request)
            resp.request_id = request.request_id
            self._audit(
                request,
                outcome="success" if resp.success else "failure",
            )
            return resp
        except Exception as exc:
            self._audit(request, outcome="error")
            return APIResponse.error(
                APIErrorCode.INTERNAL_ERROR,
                f"Internal error in {request.endpoint}: {exc}",
                request_id=request.request_id,
            )

    # ------------------------------------------------------------------
    # Audit helper
    # ------------------------------------------------------------------

    def _audit(
        self,
        req: APIRequest,
        outcome: str = "success",
        justification: str = "",
    ) -> None:
        """Append one ACTION_EXECUTED event to the ledger for this request."""
        try:
            self._ledger.append(
                AuditEvent(
                    event_type    = EventType.ACTION_EXECUTED,
                    actor         = req.caller_id or "anonymous",
                    action        = req.endpoint,
                    outcome       = outcome,
                    user_id       = req.caller_id,
                    session_id    = req.session_id,
                    jti           = req.jti,
                    justification = justification or req.endpoint,
                    metadata      = {"request_id": req.request_id},
                )
            )
        except Exception:
            pass  # never let ledger errors break the API

    # ------------------------------------------------------------------
    # Route registration
    # ------------------------------------------------------------------

    def _register_routes(self) -> None:
        r = self._routes
        r["/v1/os/status"]            = self._os_status
        r["/v1/os/health"]            = self._os_health
        r["/v1/os/version"]           = self._os_version
        r["/v1/os/schumann"]          = self._os_schumann
        r["/v1/gaian/birth/begin"]    = self._gaian_birth_begin
        r["/v1/gaian/birth/answer"]   = self._gaian_birth_answer
        r["/v1/gaian/birth/complete"] = self._gaian_birth_complete
        r["/v1/gaian/status"]         = self._gaian_status
        r["/v1/gaian/name"]           = self._gaian_name
        r["/v1/gaian/list"]           = self._gaian_list
        r["/v1/session/begin"]        = self._session_begin
        r["/v1/session/turn"]         = self._session_turn
        r["/v1/session/end"]          = self._session_end
        r["/v1/session/status"]       = self._session_status
        r["/v1/memory/remember"]      = self._memory_remember
        r["/v1/memory/recall"]        = self._memory_recall
        r["/v1/memory/stats"]         = self._memory_stats
        r["/v1/memory/consolidate"]   = self._memory_consolidate
        r["/v1/avatar/waveform"]      = self._avatar_waveform
        r["/v1/fs/stats"]             = self._fs_stats
        r["/v1/fs/integrity"]         = self._fs_integrity

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

    def _require_runtime(self, req: APIRequest, gaian_id: str) -> tuple:
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
        if req.caller_id not in (gaian_id, "gaia", "system"):
            return APIResponse.error(
                APIErrorCode.AUTONOMY_VIOLATION,
                f"Autonomy violation: caller '{req.caller_id}' may not act "
                f"on behalf of GAIAN '{gaian_id}'.",
                request_id=req.request_id,
            )
        return None

    # ------------------------------------------------------------------
    # OS endpoints
    # ------------------------------------------------------------------

    def _os_status(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check:
            return check
        return APIResponse.ok("GAIA OS is live.", payload=self._session.status())

    def _os_health(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check:
            return check
        healthy = self._session.is_healthy
        return APIResponse(
            success=healthy,
            code=APIErrorCode.OK if healthy else APIErrorCode.NOT_READY,
            message="GAIA OS healthy." if healthy else "GAIA OS degraded.",
            payload={
                "healthy":     healthy,
                "degraded":    self._session.is_degraded,
                "boot_status": self._session.boot_status.value,
            },
        )

    def _os_version(self, req: APIRequest) -> APIResponse:
        return APIResponse.ok(
            "GAIA OS version.",
            payload={
                "api_version": GAIA_API_VERSION,
                "os_version":  GAIA_OS_VERSION,
                "name":        PrimordialSession.GAIA_NAME,
            },
        )

    def _os_schumann(self, req: APIRequest) -> APIResponse:
        from core.identity.avatar.elemental import GAIA_SCHUMANN_HZ, GAIA_WAVEFORM
        return APIResponse.ok(
            "Schumann resonance status.",
            payload={
                "frequency_hz":  GAIA_SCHUMANN_HZ,
                "confirmed":     GAIA_WAVEFORM.frequency_hz == 7.83,
                "waveform_shape": GAIA_WAVEFORM.waveform_shape,
                "elements":      [e.value for e in GAIA_WAVEFORM.harmonic_elements],
                "description":   GAIA_WAVEFORM.description,
            },
        )

    # ------------------------------------------------------------------
    # GAIAN birth endpoints
    # ------------------------------------------------------------------

    _ceremonies: Dict[str, BirthCeremony] = {}

    def _gaian_birth_begin(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check:
            return check
        ceremony = BirthCeremony(self._session.registry)
        guardian_ids = req.payload.get("guardian_gaian_ids")
        gaian_id = ceremony.begin(guardian_gaian_ids=guardian_ids)
        self._ceremonies[gaian_id] = ceremony
        self._ledger.append(AuditEvent(
            event_type    = EventType.SESSION_START,
            actor         = req.caller_id,
            action        = "birth_ceremony_begin",
            outcome       = "success",
            session_id    = gaian_id,
            jti           = req.jti,
            justification = "GAIAN birth ceremony initiated",
        ))
        return APIResponse.ok(
            "Birth ceremony begun. GAIAN awaits their first conversation.",
            payload={
                "gaian_id":    gaian_id,
                "ceremony_id": gaian_id,
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
        if check:
            return check
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
        followup  = ceremony.answer(question_id, answer)
        remaining = [q.question_id for q in ceremony.remaining()]
        return APIResponse.ok(
            "Answer recorded.",
            payload={
                "followup_prompt":     followup,
                "remaining_questions": remaining,
                "ready_to_complete":   ceremony._questionnaire.is_ready_to_complete(),
            },
        )

    def _gaian_birth_complete(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check:
            return check
        ceremony_id = req.payload.get("ceremony_id", "")
        ceremony    = self._ceremonies.get(ceremony_id)
        if not ceremony:
            return APIResponse.error(
                APIErrorCode.NOT_FOUND,
                f"No active birth ceremony for ceremony_id '{ceremony_id}'.",
            )
        identity = ceremony.complete()
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
        if self._fs:
            home = self._fs.gaian_home(identity.gaian_id)
            home.save_identity(identity.summary())
            if ceremony.genesis_record:
                try:
                    home.save_genesis(ceremony.genesis_record.summary())
                except PermissionError:
                    pass
        del self._ceremonies[ceremony_id]
        self._ledger.append(AuditEvent(
            event_type    = EventType.IDENTITY_VERIFIED,
            actor         = "gaia",
            action        = "birth_ceremony_complete",
            outcome       = "success",
            user_id       = identity.gaian_id,
            session_id    = identity.gaian_id,
            jti           = req.jti,
            justification = "GAIAN identity established via birth ceremony",
        ))
        return APIResponse.ok(
            "Birth ceremony complete. The GAIAN exists. They have not yet chosen their name.",
            payload={
                "gaian_id":       identity.gaian_id,
                "is_named":       identity.is_named(),
                "lifecycle_stage": identity.lifecycle_stage.value
                if identity.lifecycle_stage else None,
                "element":        _extract_element(identity),
                "avatar_summary": identity.avatar.summary() if identity.avatar else {},
                "soul_word":      ceremony.genesis_record.soul_word
                if ceremony.genesis_record else None,
            },
        )

    # ------------------------------------------------------------------
    # GAIAN identity endpoints
    # ------------------------------------------------------------------

    def _gaian_status(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check:
            return check
        gaian_id = req.payload.get("gaian_id", "")
        rt, err  = self._require_runtime(req, gaian_id)
        if err:
            return err
        return APIResponse.ok(f"GAIAN status for '{gaian_id}'.", payload=rt.status())

    def _gaian_name(self, req: APIRequest) -> APIResponse:
        """
        The GAIAN chooses their own name.
        Only the GAIAN themselves or system may call this.
        Hook fired: 'gaian_named'
        """
        check = self._require_session(req)
        if check:
            return check
        gaian_id = req.payload.get("gaian_id", "")
        name     = req.payload.get("name", "").strip()
        if not name:
            return APIResponse.error(APIErrorCode.VALIDATION_ERROR, "name is required.")
        autonomy_check = self._require_caller_is_gaian(req, gaian_id)
        if autonomy_check:
            return autonomy_check
        rt, err = self._require_runtime(req, gaian_id)
        if err:
            return err
        confirmation = rt.choose_name(name)
        if self._fs:
            home = self._fs.gaian_home(gaian_id)
            home.save_identity(rt.identity.summary())
        self._session.on_gaian_named(gaian_id, name)
        return APIResponse.ok(
            confirmation,
            payload={
                "gaian_id": gaian_id,
                "name":     name,
                "is_named": rt.identity.is_named(),
            },
        )

    def _gaian_list(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check:
            return check
        gaians = [
            {
                "gaian_id":      g.gaian_id,
                "display_name":  g.display_name,
                "is_named":      g.is_named(),
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
        if check:
            return check
        gaian_id = req.payload.get("gaian_id", "")
        human_id = req.payload.get("human_id", "")
        rt, err  = self._require_runtime(req, gaian_id)
        if err:
            return err
        session = rt.begin_session(human_id=human_id)
        log_auth_event(
            actor      = req.caller_id,
            action     = "session_begin",
            outcome    = "success",
            user_id    = human_id or req.caller_id,
            jti        = req.jti,
            session_id = session.session_id,
            ledger     = self._ledger,
        )
        return APIResponse.ok(
            "Session begun.",
            payload={
                "session_id": session.session_id,
                "gaian_id":   gaian_id,
                "started_at": session.started_at,
            },
        )

    def _session_turn(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check:
            return check
        gaian_id = req.payload.get("gaian_id", "")
        content  = req.payload.get("content", "").strip()
        modality = req.payload.get("modality", "text")
        human_id = req.payload.get("human_id", "")
        if not content:
            return APIResponse.error(APIErrorCode.VALIDATION_ERROR, "content is required.")
        rt, err = self._require_runtime(req, gaian_id)
        if err:
            return err
        try:
            mod = InputModality(modality)
        except ValueError:
            mod = InputModality.TEXT
        response = rt.turn(content, modality=mod, human_id=human_id)
        return APIResponse.ok(
            "Turn complete.",
            payload={
                "response":       response,
                "turn":           rt.current_session.turn_count
                if rt.current_session else 0,
                "cognitive_state": rt.cognitive_state.summary(),
            },
        )

    def _session_end(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check:
            return check
        gaian_id = req.payload.get("gaian_id", "")
        rt, err  = self._require_runtime(req, gaian_id)
        if err:
            return err
        ended = rt.end_session()
        if not ended:
            return APIResponse.error(
                APIErrorCode.SESSION_NOT_ACTIVE, "No active session to end."
            )
        log_auth_event(
            actor      = req.caller_id,
            action     = "session_end",
            outcome    = "success",
            user_id    = req.caller_id,
            jti        = req.jti,
            session_id = ended.session_id,
            ledger     = self._ledger,
        )
        return APIResponse.ok(
            "Session ended.",
            payload={
                "session_id": ended.session_id,
                "turns":      ended.turn_count,
                "ended_at":   ended.ended_at,
            },
        )

    def _session_status(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check:
            return check
        gaian_id = req.payload.get("gaian_id", "")
        rt, err  = self._require_runtime(req, gaian_id)
        if err:
            return err
        session = rt.current_session
        if not session or not session.is_active:
            return APIResponse.error(
                APIErrorCode.SESSION_NOT_ACTIVE, "No active session."
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
        if check:
            return check
        gaian_id   = req.payload.get("gaian_id", "")
        content    = req.payload.get("content", "").strip()
        kind_str   = req.payload.get("kind", "session_context")
        importance = float(req.payload.get("importance", 0.5))
        autonomy_check = self._require_caller_is_gaian(req, gaian_id)
        if autonomy_check:
            return autonomy_check
        rt, err = self._require_runtime(req, gaian_id)
        if err:
            return err
        try:
            kind = MemoryKind(kind_str)
        except ValueError:
            kind = MemoryKind.SESSION_CONTEXT
        fragment = rt.memory.remember(
            content, kind=kind,
            scope=MemoryScope.LIFETIME, importance=importance,
        )
        if not fragment:
            return APIResponse.error(APIErrorCode.VALIDATION_ERROR, "Memory content is empty.")
        self._ledger.append(AuditEvent(
            event_type    = EventType.MEMORY_WRITE,
            actor         = req.caller_id,
            action        = "memory_remember",
            outcome       = "success",
            user_id       = gaian_id,
            session_id    = req.session_id,
            jti           = req.jti,
            justification = f"kind={kind.value} importance={importance}",
            metadata      = {"fragment_id": fragment.fragment_id},
        ))
        return APIResponse.ok(
            "Memory stored.",
            payload={"fragment_id": fragment.fragment_id, "kind": kind.value},
        )

    def _memory_recall(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check:
            return check
        gaian_id = req.payload.get("gaian_id", "")
        autonomy_check = self._require_caller_is_gaian(req, gaian_id)
        if autonomy_check:
            return autonomy_check
        rt, err = self._require_runtime(req, gaian_id)
        if err:
            return err
        limit          = int(req.payload.get("limit", 10))
        min_importance = float(req.payload.get("min_importance", 0.0))
        fragments = rt.memory.recall(min_importance=min_importance, limit=limit)
        self._ledger.append(AuditEvent(
            event_type    = EventType.MEMORY_READ,
            actor         = req.caller_id,
            action        = "memory_recall",
            outcome       = "success",
            user_id       = gaian_id,
            session_id    = req.session_id,
            jti           = req.jti,
            justification = f"limit={limit}",
        ))
        return APIResponse.ok(
            f"{len(fragments)} memory fragment(s) recalled.",
            payload={
                "fragments": [f.summary() for f in fragments],
                "count":     len(fragments),
            },
        )

    def _memory_stats(self, req: APIRequest) -> APIResponse:
        check = self._require_session(req)
        if check:
            return check
        gaian_id = req.payload.get("gaian_id", "")
        autonomy_check = self._require_caller_is_gaian(req, gaian_id)
        if autonomy_check:
            return autonomy_check
        rt, err = self._require_runtime(req, gaian_id)
        if err:
            return err
        return APIResponse.ok("Memory stats.", payload=rt.memory.stats())

    def _memory_consolidate(self, req: APIRequest) -> APIResponse:
        """
        Consolidate fragments into a memory epoch.
        Hook fired: 'epoch_closed'
        """
        check = self._require_session(req)
        if check:
            return check
        gaian_id = req.payload.get("gaian_id", "")
        summary  = req.payload.get("summary", "")
        autonomy_check = self._require_caller_is_gaian(req, gaian_id)
        if autonomy_check:
            return autonomy_check
        rt, err = self._require_runtime(req, gaian_id)
        if err:
            return err
        if not summary:
            return APIResponse.error(APIErrorCode.VALIDATION_ERROR, "summary is required.")
        epoch = rt.memory.consolidate(summary=summary)
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
        if check:
            return check
        gaian_id = req.payload.get("gaian_id", "")
        rt, err  = self._require_runtime(req, gaian_id)
        if err:
            return err
        avatar = rt.identity.avatar
        if not avatar:
            return APIResponse.error(APIErrorCode.NOT_FOUND, "No avatar found for this GAIAN.")
        return APIResponse.ok("Waveform avatar state.", payload=avatar.summary())

    # ------------------------------------------------------------------
    # Filesystem endpoints
    # ------------------------------------------------------------------

    def _fs_stats(self, req: APIRequest) -> APIResponse:
        if not self._fs:
            return APIResponse.error(APIErrorCode.NOT_READY, "Filesystem not wired.")
        return APIResponse.ok("Filesystem stats.", payload=self._fs.stats())

    def _fs_integrity(self, req: APIRequest) -> APIResponse:
        if not self._fs:
            return APIResponse.error(APIErrorCode.NOT_READY, "Filesystem not wired.")
        results  = self._fs.verify_all_homes()
        all_clean = all(len(v) == 0 for v in results.values())
        return APIResponse(
            success=all_clean,
            code=APIErrorCode.OK if all_clean else APIErrorCode.INTERNAL_ERROR,
            message="All homes clean." if all_clean else "Integrity issues detected.",
            payload={"results": results, "all_clean": all_clean},
        )


# ---------------------------------------------------------------------------
# FastAPI application factory  —  create_app()
# ---------------------------------------------------------------------------


def create_app(
    session: Optional[PrimordialSession] = None,
    filesystem: Optional[GAIAFilesystem] = None,
    ledger: Optional[ActionLedger] = None,
) -> "fastapi.FastAPI":
    """
    Build and return a fully-wired FastAPI application.

    Mounts:
        /v1/*        — GAIAOSApi dispatch (via HTTP bridge)
        /audit/*     — audit_router  (ledger query endpoints)
        /health      — lightweight liveness probe

    Auth middleware:
        Reads Authorization: Bearer <token> or X-GAIA-Token: <token>.
        Calls log_auth_event() for every validated request.
        Returns 401 if token is missing on protected routes.
    """
    import os
    import fastapi
    from fastapi import Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from core.audit.ledger import audit_router

    # Resolve ledger
    _ledger = ledger or get_default_ledger()

    # Wire internal router
    api = GAIAOSApi(ledger=_ledger)
    if session:
        api.wire(session=session, filesystem=filesystem, ledger=_ledger)

    app = fastapi.FastAPI(
        title="GAIA OS API",
        version=GAIA_OS_VERSION,
        description="Sovereign integration surface for GAIA-OS.",
    )

    # CORS — tighten origins in production via GAIA_CORS_ORIGINS env var
    origins = os.environ.get("GAIA_CORS_ORIGINS", "*").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Auth middleware — extracts JTI, logs auth events
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        token = (
            request.headers.get("X-GAIA-Token")
            or (request.headers.get("Authorization", "").removeprefix("Bearer ").strip() or None)
        )
        jti = ""
        if token:
            try:
                import jwt as _jwt
                secret = os.environ.get("GAIA_JWT_SECRET", "")
                if secret:
                    claims = _jwt.decode(token, secret, algorithms=["HS256"])
                    jti = claims.get("jti", "")
                    log_auth_event(
                        actor   = claims.get("sub", "unknown"),
                        action  = f"request:{request.method}:{request.url.path}",
                        outcome = "success",
                        user_id = claims.get("sub", ""),
                        jti     = jti,
                        ledger  = _ledger,
                    )
            except Exception as exc:
                log_auth_event(
                    actor   = "unknown",
                    action  = f"request:{request.method}:{request.url.path}",
                    outcome = "token_invalid",
                    metadata= {"error": str(exc)},
                    ledger  = _ledger,
                )
        request.state.jti = jti
        return await call_next(request)

    # HTTP bridge — translates HTTP POST /v1/* into GAIAOSApi.dispatch()
    @app.post("/v1/{path:path}")
    async def v1_dispatch(path: str, request: Request) -> JSONResponse:
        body = await request.json() if await request.body() else {}
        caller_id  = body.pop("caller_id", "anonymous")
        session_id = body.pop("session_id", "")
        api_request = APIRequest(
            caller_id  = caller_id,
            endpoint   = f"/v1/{path}",
            payload    = body,
            jti        = getattr(request.state, "jti", ""),
            session_id = session_id,
        )
        resp = api.dispatch(api_request)
        status_code = 200 if resp.success else (
            404 if resp.code == APIErrorCode.NOT_FOUND else
            403 if resp.code in (APIErrorCode.AUTONOMY_VIOLATION, APIErrorCode.PERMISSION_DENIED) else
            401 if resp.code == APIErrorCode.UNAUTHORIZED else
            400 if resp.code == APIErrorCode.VALIDATION_ERROR else
            503 if resp.code == APIErrorCode.NOT_READY else
            500
        )
        return JSONResponse(content=resp.to_dict(), status_code=status_code)

    # Mount audit router
    app.include_router(audit_router)

    # Liveness probe
    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "version": GAIA_OS_VERSION}

    return app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _extract_element(identity) -> Optional[str]:
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
    Attaches a listener that translates internal memory events into
    named session hooks so PersistenceManager receives every fragment.
    """
    def _bridge(event: str, fragment) -> None:
        if event == "memory.fragment.written":
            session.fire_hook("fragment_written", gaian_id, fragment)
    mem.on_event(_bridge)


__all__ = [
    "GAIAOSApi",
    "APIRequest",
    "APIResponse",
    "APIErrorCode",
    "GAIA_API_VERSION",
    "GAIA_OS_VERSION",
    "create_app",
]
