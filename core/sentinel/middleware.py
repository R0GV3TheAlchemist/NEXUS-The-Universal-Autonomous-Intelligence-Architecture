"""
SentinelMiddleware — wraps GAIAOSApi.dispatch().

Usage:
    from core.sentinel.middleware import SentinelMiddleware
    from core.sentinel.sentinel import Sentinel

    sentinel = Sentinel(audit_root=Path('/data/gaia'))
    protected_api = SentinelMiddleware(api, sentinel, session)

    # Use protected_api exactly like api:
    response = protected_api.dispatch(request)

The middleware:
  1. Builds a context snapshot from the live session
  2. Calls sentinel.evaluate(request, context)
  3. If verdict.allow is False → returns a blocked APIResponse
     (never calls the underlying api.dispatch)
  4. If verdict.allow is True → calls api.dispatch, attaches
     any Sentinel warnings to the response payload, then runs
     post-response hooks (e.g. AutonomyProbeRule needs the
     response code to detect repeated violations)
  5. Updates the context with the response for post-response rules
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from core.api.api import APIErrorCode, APIRequest, APIResponse
from core.sentinel.sentinel import Sentinel
from core.sentinel.threat import ThreatLevel

logger = logging.getLogger("gaia.sentinel.middleware")


class SentinelMiddleware:
    """
    A drop-in wrapper around GAIAOSApi that applies Sentinel
    evaluation before and after every dispatch call.
    """

    def __init__(
        self,
        api,                   # GAIAOSApi
        sentinel: Sentinel,
        session,               # PrimordialSession
    ) -> None:
        self._api      = api
        self._sentinel = sentinel
        self._session  = session
        # Mutable context shared across calls (for post-response hooks)
        self._ctx: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Public interface — same signature as GAIAOSApi.dispatch
    # ------------------------------------------------------------------

    def dispatch(self, request: APIRequest) -> APIResponse:
        context = self._build_context(request)

        # Pre-dispatch evaluation
        verdict = self._sentinel.evaluate(request, context)

        if not verdict.allow:
            logger.warning(
                "Sentinel BLOCKED %s from %s: %s",
                request.endpoint, request.caller_id, verdict.block_reason,
            )
            return self._blocked_response(request, verdict)

        # Proceed
        response = self._api.dispatch(request)

        # Post-dispatch: update context so post-response rules can fire
        self._ctx["last_response_code"]    = response.code.value
        self._ctx["last_response_payload"] = response.payload

        # Re-evaluate post-response rules (e.g. autonomy probe
        # needs the response code to know a violation occurred)
        post_verdict = self._sentinel.evaluate(request, self._ctx)
        if not post_verdict.allow:
            # The request already succeeded, but escalate to CRITICAL
            # means we alert and log — we do NOT retroactively block.
            logger.critical(
                "Sentinel post-response escalation on %s: %s",
                request.endpoint, post_verdict.block_reason,
            )

        # Attach warnings to the response payload if verdict was WARN
        if verdict.warning and response.success:
            response.payload["_sentinel_warning"] = verdict.warning

        return response

    # ------------------------------------------------------------------
    # Context builder
    # ------------------------------------------------------------------

    def _build_context(self, request: APIRequest) -> Dict[str, Any]:
        """
        Build the context snapshot the rules read from.
        Pulls live data from the session without coupling rules
        to the session directly.
        """
        ctx = dict(self._ctx)  # carry forward post-response state

        # Expose live runtimes for CognitiveOverloadRule
        if hasattr(self._session, "_runtimes"):
            ctx["runtimes"] = self._session._runtimes

        # Expose session registry
        if hasattr(self._session, "registry"):
            ctx["registry"] = self._session.registry

        # Expose manifest
        if hasattr(self._session, "manifest"):
            ctx["manifest"] = self._session.manifest

        return ctx

    # ------------------------------------------------------------------
    # Blocked response factory
    # ------------------------------------------------------------------

    @staticmethod
    def _blocked_response(
        request: APIRequest,
        verdict,
    ) -> APIResponse:
        level = verdict.level
        if level == ThreatLevel.CRITICAL:
            code = APIErrorCode.PERMISSION_DENIED
            msg  = f"[SENTINEL CRITICAL] {verdict.block_reason}"
        elif level == ThreatLevel.BLOCK:
            # Distinguish rate-limit (429-like) from autonomy (403)
            from core.sentinel.threat import ThreatCategory
            is_rate = any(
                e.category in (
                    ThreatCategory.RATE_LIMIT,
                    ThreatCategory.COGNITIVE_OVERLOAD,
                )
                for e in verdict.events
            )
            code = APIErrorCode.PERMISSION_DENIED
            msg  = f"[SENTINEL] {verdict.block_reason}"
        else:
            code = APIErrorCode.PERMISSION_DENIED
            msg  = verdict.block_reason

        return APIResponse(
            success=False,
            code=code,
            message=msg,
            payload={
                "sentinel_level":  level.value,
                "sentinel_events": [
                    {"rule": e.rule_name, "description": e.description}
                    for e in verdict.events
                ],
            },
            request_id=getattr(request, "request_id", ""),
        )
