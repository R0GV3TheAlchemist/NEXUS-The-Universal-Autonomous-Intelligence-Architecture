"""
core/registry/capability_registry.py

Tool & Capability Registry — Issue #230
Versioned catalog of every agent tool and API GAIA can invoke.
Every tool must be registered here before it can be invoked.

Canon ref: C01 (Gaian sovereignty), C32 (Synergy Doctrine)
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable

logger = logging.getLogger("gaia.registry")


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ToolStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class FallbackBehavior(str, Enum):
    RAISE = "raise"          # Raise an error immediately
    SKIP = "skip"            # Skip the tool call silently
    USE_CACHE = "use_cache"  # Return last cached result
    USE_FALLBACK = "use_fallback"  # Route to fallback tool


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ToolSchema:
    """Lightweight input/output schema for a registered tool."""
    input_fields: list[str] = field(default_factory=list)
    output_fields: list[str] = field(default_factory=list)
    required_inputs: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "input_fields": self.input_fields,
            "output_fields": self.output_fields,
            "required_inputs": self.required_inputs,
            "description": self.description,
        }


@dataclass
class RegistryEntry:
    """A single versioned tool entry in the capability registry."""
    name: str
    version: str
    description: str
    permission_scope: str
    schema: ToolSchema = field(default_factory=ToolSchema)
    health_check_fn: Callable[[], bool] | None = None
    fallback_behavior: FallbackBehavior = FallbackBehavior.RAISE
    fallback_tool: str | None = None
    tags: list[str] = field(default_factory=list)
    # Runtime state (not persisted)
    status: ToolStatus = ToolStatus.UNKNOWN
    last_verified: str | None = None
    last_health_check: str | None = None
    # Version history
    changelog: list[dict] = field(default_factory=list)
    registered_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self, include_fn: bool = False) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "permission_scope": self.permission_scope,
            "schema": self.schema.to_dict(),
            "fallback_behavior": self.fallback_behavior.value,
            "fallback_tool": self.fallback_tool,
            "tags": self.tags,
            "status": self.status.value,
            "last_verified": self.last_verified,
            "last_health_check": self.last_health_check,
            "changelog": self.changelog,
            "registered_at": self.registered_at,
        }

    def record_version_change(self, old_version: str, reason: str) -> None:
        self.changelog.append({
            "from_version": old_version,
            "to_version": self.version,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": reason,
        })


@dataclass
class HealthCheckResult:
    tool_name: str
    healthy: bool
    status: ToolStatus
    checked_at: str
    error: str | None = None


# ---------------------------------------------------------------------------
# Capability Registry
# ---------------------------------------------------------------------------

class CapabilityRegistry:
    """
    The single source of truth for all GAIA tools and capabilities.

    Every tool MUST be registered here before an agent can invoke it.
    Unregistered tool invocations are blocked and logged.

    Usage:
        registry = CapabilityRegistry()
        registry.register(RegistryEntry(
            name="read_memory",
            version="1.0.0",
            description="Read from GAIA sovereign memory.",
            permission_scope="read:memory",
        ))

        entry = registry.get("read_memory")   # Returns entry or raises
        tools = registry.query(tags=["memory"]) # Filter by tags
        await registry.run_health_checks()      # Check all tools
    """

    def __init__(
        self,
        persist_path: Path | None = None,
        health_check_interval_seconds: int = 300,
    ):
        self._entries: dict[str, RegistryEntry] = {}
        self._blocked_log: list[dict] = []
        self.persist_path = persist_path or Path("data/registry/capability_registry.json")
        self.health_check_interval = health_check_interval_seconds
        self._health_task: asyncio.Task | None = None

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, entry: RegistryEntry) -> None:
        """
        Register a tool. If the tool already exists with a different
        version, the change is recorded in the changelog.
        """
        existing = self._entries.get(entry.name)
        if existing and existing.version != entry.version:
            entry.changelog = existing.changelog.copy()
            entry.record_version_change(
                old_version=existing.version,
                reason="Re-registered with new version.",
            )
            logger.info(
                f"Tool '{entry.name}' updated: {existing.version} → {entry.version}"
            )
        elif existing:
            logger.debug(f"Tool '{entry.name}' re-registered (same version).")
        else:
            logger.info(f"Tool '{entry.name}' v{entry.version} registered.")

        self._entries[entry.name] = entry
        self._persist()

    def deregister(self, tool_name: str) -> None:
        """Remove a tool from the registry."""
        if tool_name in self._entries:
            del self._entries[tool_name]
            logger.info(f"Tool '{tool_name}' deregistered.")
            self._persist()
        else:
            logger.warning(f"deregister: '{tool_name}' not found in registry.")

    def update_version(
        self,
        tool_name: str,
        new_version: str,
        reason: str = "Version bump.",
    ) -> None:
        """Update a tool's version and record in changelog."""
        entry = self._require(tool_name)
        old_version = entry.version
        entry.version = new_version
        entry.record_version_change(old_version, reason)
        self._persist()
        logger.info(f"Tool '{tool_name}' version updated: {old_version} → {new_version}")

    # ------------------------------------------------------------------
    # Query API — agents use this to discover available tools
    # ------------------------------------------------------------------

    def get(self, tool_name: str) -> RegistryEntry:
        """Get a tool entry. Raises KeyError if not registered."""
        return self._require(tool_name)

    def exists(self, tool_name: str) -> bool:
        """Return True if the tool is registered."""
        return tool_name in self._entries

    def query(
        self,
        tags: list[str] | None = None,
        scope: str | None = None,
        status: ToolStatus | None = None,
        healthy_only: bool = False,
    ) -> list[RegistryEntry]:
        """
        Query the registry with optional filters.

        Args:
            tags: Return tools that have ALL of these tags.
            scope: Return tools with this permission scope.
            status: Return tools with this status.
            healthy_only: Return only HEALTHY tools.
        """
        results = list(self._entries.values())

        if tags:
            results = [e for e in results if all(t in e.tags for t in tags)]
        if scope:
            results = [e for e in results if e.permission_scope == scope]
        if status:
            results = [e for e in results if e.status == status]
        if healthy_only:
            results = [e for e in results if e.status == ToolStatus.HEALTHY]

        return results

    def list_all(self) -> list[dict]:
        """Return all registered tools as serializable dicts."""
        return [e.to_dict() for e in self._entries.values()]

    def changelog_for(self, tool_name: str) -> list[dict]:
        """Return full version history for a tool."""
        return self._require(tool_name).changelog

    # ------------------------------------------------------------------
    # Unregistered tool enforcement
    # ------------------------------------------------------------------

    def assert_registered(self, tool_name: str) -> RegistryEntry:
        """
        Called by agents before invoking any tool.
        Blocks and logs unregistered tool invocations.
        Raises UnregisteredToolError if not found.
        """
        if tool_name not in self._entries:
            self._log_blocked(tool_name)
            raise UnregisteredToolError(tool_name)
        entry = self._entries[tool_name]
        entry.last_verified = datetime.now(timezone.utc).isoformat()
        return entry

    def get_blocked_log(self) -> list[dict]:
        """Return log of all attempted unregistered tool invocations."""
        return list(self._blocked_log)

    # ------------------------------------------------------------------
    # Health checks
    # ------------------------------------------------------------------

    def run_health_check(self, tool_name: str) -> HealthCheckResult:
        """Run health check for a single tool synchronously."""
        entry = self._require(tool_name)
        checked_at = datetime.now(timezone.utc).isoformat()

        if entry.health_check_fn is None:
            entry.status = ToolStatus.UNKNOWN
            entry.last_health_check = checked_at
            return HealthCheckResult(
                tool_name=tool_name,
                healthy=True,
                status=ToolStatus.UNKNOWN,
                checked_at=checked_at,
            )

        try:
            healthy = entry.health_check_fn()
            entry.status = ToolStatus.HEALTHY if healthy else ToolStatus.UNAVAILABLE
            entry.last_health_check = checked_at
            logger.debug(f"Health check '{tool_name}': {entry.status.value}")
            return HealthCheckResult(
                tool_name=tool_name,
                healthy=healthy,
                status=entry.status,
                checked_at=checked_at,
            )
        except Exception as exc:
            entry.status = ToolStatus.DEGRADED
            entry.last_health_check = checked_at
            logger.warning(f"Health check '{tool_name}' raised: {exc}")
            return HealthCheckResult(
                tool_name=tool_name,
                healthy=False,
                status=ToolStatus.DEGRADED,
                checked_at=checked_at,
                error=str(exc),
            )

    async def run_health_checks(self) -> list[HealthCheckResult]:
        """Run health checks for all registered tools asynchronously."""
        loop = asyncio.get_event_loop()
        results = []
        for name in list(self._entries):
            result = await loop.run_in_executor(None, self.run_health_check, name)
            results.append(result)
        return results

    async def start_periodic_health_checks(self) -> None:
        """Start background task that runs health checks on the configured interval."""
        async def _loop():
            while True:
                await asyncio.sleep(self.health_check_interval)
                logger.info("Running periodic health checks...")
                await self.run_health_checks()

        self._health_task = asyncio.create_task(_loop())
        logger.info(
            f"Periodic health checks started (interval: {self.health_check_interval}s)"
        )

    def stop_periodic_health_checks(self) -> None:
        """Stop the background health check task."""
        if self._health_task and not self._health_task.done():
            self._health_task.cancel()
            logger.info("Periodic health checks stopped.")

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _persist(self) -> None:
        """Save registry snapshot to disk (health_check_fn is not serialized)."""
        try:
            self.persist_path.parent.mkdir(parents=True, exist_ok=True)
            snapshot = {name: entry.to_dict() for name, entry in self._entries.items()}
            with self.persist_path.open("w", encoding="utf-8") as f:
                json.dump(snapshot, f, indent=2)
        except Exception as exc:
            logger.error(f"Registry persist failed: {exc}")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require(self, tool_name: str) -> RegistryEntry:
        entry = self._entries.get(tool_name)
        if entry is None:
            raise KeyError(f"Tool '{tool_name}' is not registered in the capability registry.")
        return entry

    def _log_blocked(self, tool_name: str) -> None:
        record = {
            "blocked_id": str(uuid.uuid4()),
            "tool_name": tool_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "reason": "Tool not registered in capability registry.",
        }
        self._blocked_log.append(record)
        logger.warning(
            f"BLOCKED unregistered tool invocation: '{tool_name}'"
        )


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------

class UnregisteredToolError(Exception):
    """Raised when an agent attempts to invoke a tool not in the registry."""

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        super().__init__(
            f"Tool '{tool_name}' is not registered in the GAIA Capability Registry. "
            f"Register it via CapabilityRegistry.register() before invocation."
        )


# ---------------------------------------------------------------------------
# Module-level singleton (importable directly)
# ---------------------------------------------------------------------------

_registry: CapabilityRegistry | None = None


def get_registry() -> CapabilityRegistry:
    """Return the module-level singleton registry."""
    global _registry
    if _registry is None:
        _registry = CapabilityRegistry()
        _bootstrap_default_tools(_registry)
    return _registry


def _bootstrap_default_tools(registry: CapabilityRegistry) -> None:
    """Bootstrap all default GAIA tools from default_policies into the registry."""
    from core.policy.default_policies import DEFAULT_TOOL_POLICIES

    for policy in DEFAULT_TOOL_POLICIES:
        if not registry.exists(policy.tool_name):
            registry.register(RegistryEntry(
                name=policy.tool_name,
                version="1.0.0",
                description=policy.description,
                permission_scope=policy.required_scope.value,
                tags=["default", policy.risk_level.value],
                fallback_behavior=FallbackBehavior.RAISE,
            ))
    logger.info(f"Bootstrapped {len(DEFAULT_TOOL_POLICIES)} default tools into registry.")
