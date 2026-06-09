"""
core/action_gate.py

The ActionGate — mandatory pre-action gate for every GAIA agent tool call.

Every agent action MUST pass through this gate before execution.
This is the enforcement point for the Trust & Permission Policy Engine (#229).

Usage (sync):
    gate = ActionGate(session_id="abc", agent_id="planner")
    gate.pre_approve_scope(PermissionScope.READ_MEMORY)

    with gate.guard("read_memory", context={"key": "user_prefs"}):
        result = read_memory("user_prefs")

Usage (async):
    async with gate.async_guard("write_file", context={"path": "canon/new.md"}):
        await write_file(...)

If the action is denied, ActionDeniedError is raised.
If approval is required and no callback is set, ActionPendingApprovalError is raised.

Canon ref: C01 (Gaian sovereignty), SOVEREIGNTY.md
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import Any, Callable

from core.policy.trust_policy_engine import (
    PermissionScope,
    PolicyDecision,
    TrustPolicyEngine,
)

logger = logging.getLogger("gaia.action_gate")


class ActionDeniedError(PermissionError):
    """Raised when a GAIA agent action is denied by policy."""

    def __init__(self, tool_name: str, reason: str):
        self.tool_name = tool_name
        self.reason = reason
        super().__init__(f"Action denied: '{tool_name}' — {reason}")


class ActionPendingApprovalError(Exception):
    """Raised when an action requires Gaian approval and no callback is configured."""

    def __init__(self, tool_name: str, approval_prompt: str, record_id: str):
        self.tool_name = tool_name
        self.approval_prompt = approval_prompt
        self.record_id = record_id
        super().__init__(
            f"Action '{tool_name}' requires Gaian approval. "
            f"Record ID: {record_id}\n{approval_prompt}"
        )


class ActionGate:
    """
    Wraps TrustPolicyEngine into a clean context-manager interface.
    Every GAIA agent tool call must use this gate.
    """

    def __init__(
        self,
        session_id: str,
        agent_id: str,
        approval_callback: Callable[[str, str], bool] | None = None,
    ):
        """
        Args:
            session_id: Current GAIA session ID.
            agent_id: Identifier for the calling agent (e.g. 'planner', 'executor').
            approval_callback: Optional sync function(tool_name, prompt) -> bool.
                               If set, called when approval is needed instead of raising.
        """
        self.session_id = session_id
        self.agent_id = agent_id
        self.approval_callback = approval_callback
        self.engine = TrustPolicyEngine(
            session_id=session_id,
            agent_id=agent_id,
        )

    def pre_approve_scope(self, scope: PermissionScope) -> None:
        """Gaian pre-approves a scope for this session."""
        self.engine.pre_approve_scope(scope)

    def revoke_scope(self, scope: PermissionScope) -> None:
        """Gaian revokes a pre-approved scope."""
        self.engine.revoke_scope(scope)

    def check(self, tool_name: str, context: dict[str, Any] | None = None) -> bool:
        """
        Evaluate policy and handle the result.
        Returns True if allowed, raises on deny or pending approval.
        """
        result = self.engine.evaluate(tool_name, context)

        if result.decision == PolicyDecision.ALLOW:
            return True

        if result.decision == PolicyDecision.DENY:
            raise ActionDeniedError(tool_name=tool_name, reason=result.reason)

        if result.decision == PolicyDecision.REQUIRE_APPROVAL:
            if self.approval_callback is not None:
                approved = self.approval_callback(tool_name, result.approval_prompt or "")
                if approved:
                    self.engine.record_approval(
                        record_id=result.record_id, approved_by="gaian_callback"
                    )
                    return True
                else:
                    raise ActionDeniedError(
                        tool_name=tool_name,
                        reason="Gaian declined approval via callback.",
                    )
            raise ActionPendingApprovalError(
                tool_name=tool_name,
                approval_prompt=result.approval_prompt or "",
                record_id=result.record_id,
            )

        raise ActionDeniedError(tool_name=tool_name, reason="Unknown policy decision.")

    @contextlib.contextmanager
    def guard(self, tool_name: str, context: dict[str, Any] | None = None):
        """
        Sync context manager. Raises before entering if action is not permitted.

        Usage:
            with gate.guard("write_file", {"path": "canon/test.md"}):
                write_file(...)
        """
        self.check(tool_name, context)
        try:
            yield
        except Exception:
            logger.exception(f"Exception during guarded action: {tool_name}")
            raise

    @contextlib.asynccontextmanager
    async def async_guard(self, tool_name: str, context: dict[str, Any] | None = None):
        """
        Async context manager. Raises before entering if action is not permitted.

        Usage:
            async with gate.async_guard("call_github", {"endpoint": "/repos"}):
                await call_github(...)
        """
        await asyncio.get_event_loop().run_in_executor(None, self.check, tool_name, context)
        try:
            yield
        except Exception:
            logger.exception(f"Exception during async guarded action: {tool_name}")
            raise

    def get_audit_log(self) -> list[dict]:
        """Return full audit log for this session."""
        return self.engine.get_audit_log()
