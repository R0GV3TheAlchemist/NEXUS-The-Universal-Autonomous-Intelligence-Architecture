"""
GAIA Filesystem Tools — prioritized, async-ready, permission-gated.

Sits on top of filesystem.py and exposes named, callable tool objects
that the agentic loop can discover, prioritize, and dispatch.

Priority model (highest → lowest):
  CRITICAL  — system integrity, genesis, autonomy records
  HIGH      — identity, waveform, memory snapshots
  NORMAL    — epoch archives, session logs
  LOW       — introspection, stats, non-essential reads

Permission gating:
  Every tool call is checked against the GAIAPath.permission field
  and the caller's gaian_id. Violations raise FSPermissionError
  before any I/O occurs.

Result envelope:
  All tools return FSToolResult — never raise into the agentic loop.
  Failures are captured as FSToolResult(success=False, error=...).

Usage:
    registry = FSToolRegistry(fs=GAIAFilesystem())
    result = await registry.execute("read_identity", gaian_id="g-001")
    if result.success:
        print(result.data)
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import IntEnum
from typing import Any, Callable, Coroutine, Dict, List, Optional

from core.fs.filesystem import (
    FSPermission,
    GAIAFilesystem,
    GAIANHome,
    GAIAPath,
)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Priority
# ---------------------------------------------------------------------------

class FSToolPriority(IntEnum):
    """
    Execution priority for filesystem tools.
    Lower integer = higher priority (mirrors OS scheduling conventions).
    The agentic loop processes CRITICAL tools before HIGH, etc.
    """
    CRITICAL = 0
    HIGH     = 1
    NORMAL   = 2
    LOW      = 3


# ---------------------------------------------------------------------------
# Result envelope
# ---------------------------------------------------------------------------

@dataclass
class FSToolResult:
    """
    Uniform result envelope returned by every filesystem tool.

    The agentic loop consumes FSToolResult objects — it never catches
    raw exceptions from the filesystem layer. All errors are captured
    here so the loop can decide how to handle them (retry, escalate,
    log, continue).
    """
    tool_name: str
    success: bool
    gaian_id: str
    timestamp: str = field(default_factory=_utcnow)
    data: Optional[Any] = None
    path: Optional[str] = None
    error: Optional[str] = None
    error_type: Optional[str] = None

    @property
    def failed(self) -> bool:
        return not self.success

    def __repr__(self) -> str:
        status = "OK" if self.success else f"ERR({self.error_type})"
        return f"FSToolResult({self.tool_name!r}, {status}, gaian={self.gaian_id!r})"


# ---------------------------------------------------------------------------
# Permission error
# ---------------------------------------------------------------------------

class FSPermissionError(PermissionError):
    """
    Raised when a tool caller lacks permission to access a GAIAPath.
    Captured into FSToolResult before reaching the agentic loop.
    """
    def __init__(self, caller_id: str, path: GAIAPath, required: FSPermission) -> None:
        self.caller_id = caller_id
        self.gaia_path = path
        self.required = required
        super().__init__(
            f"GAIAN '{caller_id}' lacks {required.value!r} access "
            f"to '{path.label}' (owner: {path.owner_id!r}, "
            f"permission: {path.permission.value!r})"
        )


def _check_permission(caller_id: str, path: GAIAPath) -> None:
    """
    Enforce filesystem permission policy.

    Rules:
      - Owner always has access.
      - GAIA (caller_id == 'gaia') has access to GAIA_READ and PUBLIC paths.
      - PUBLIC paths are accessible to all callers.
      - Everything else is denied.
    """
    if caller_id == path.owner_id:
        return
    if path.permission == FSPermission.PUBLIC:
        return
    if caller_id == "gaia" and path.permission in (
        FSPermission.GAIA_READ, FSPermission.PUBLIC
    ):
        return
    raise FSPermissionError(caller_id, path, path.permission)


# ---------------------------------------------------------------------------
# Tool base
# ---------------------------------------------------------------------------

# Type alias for async tool handler functions
FSToolHandler = Callable[..., Coroutine[Any, Any, FSToolResult]]


@dataclass
class FSTool:
    """
    A named, prioritized, async-ready filesystem tool.

    Each tool wraps a single async handler function. The handler
    receives the GAIANHome and any kwargs passed to execute().
    The tool is registered in FSToolRegistry by name.

    Attributes:
        name        : Unique tool name used as the dispatch key.
        description : Human-readable description for agentic introspection.
        priority    : Execution priority — determines queue ordering.
        is_write    : True for write tools, False for read tools.
        handler     : Async callable (home, caller_id, **kwargs) -> FSToolResult.
    """
    name: str
    description: str
    priority: FSToolPriority
    is_write: bool
    handler: FSToolHandler

    async def execute(self, home: GAIANHome, caller_id: str, **kwargs: Any) -> FSToolResult:
        """
        Execute the tool, capturing all errors into FSToolResult.
        """
        try:
            return await self.handler(home=home, caller_id=caller_id, **kwargs)
        except FSPermissionError as exc:
            return FSToolResult(
                tool_name=self.name,
                success=False,
                gaian_id=caller_id,
                error=str(exc),
                error_type="FSPermissionError",
            )
        except FileNotFoundError as exc:
            return FSToolResult(
                tool_name=self.name,
                success=False,
                gaian_id=caller_id,
                error=str(exc),
                error_type="FileNotFoundError",
            )
        except PermissionError as exc:
            return FSToolResult(
                tool_name=self.name,
                success=False,
                gaian_id=caller_id,
                error=str(exc),
                error_type="PermissionError",
            )
        except Exception as exc:
            return FSToolResult(
                tool_name=self.name,
                success=False,
                gaian_id=caller_id,
                error=str(exc),
                error_type=type(exc).__name__,
            )

    def __repr__(self) -> str:
        rw = "write" if self.is_write else "read"
        return f"FSTool({self.name!r}, priority={self.priority.name}, {rw})"


# ---------------------------------------------------------------------------
# Built-in tool handlers
# ---------------------------------------------------------------------------

async def _read_identity(
    home: GAIANHome, caller_id: str, **_: Any
) -> FSToolResult:
    path = home.identity_file
    _check_permission(caller_id, path)
    data = home.load_identity()
    return FSToolResult(
        tool_name="read_identity",
        success=True,
        gaian_id=home.gaian_id,
        data=data,
        path=str(path),
    )


async def _write_identity(
    home: GAIANHome, caller_id: str, data: Dict[str, Any], **_: Any
) -> FSToolResult:
    path = home.identity_file
    _check_permission(caller_id, path)
    home.save_identity(data)
    return FSToolResult(
        tool_name="write_identity",
        success=True,
        gaian_id=home.gaian_id,
        path=str(path),
    )


async def _read_genesis(
    home: GAIANHome, caller_id: str, **_: Any
) -> FSToolResult:
    path = home.genesis_file
    _check_permission(caller_id, path)
    data = home.load_genesis()
    return FSToolResult(
        tool_name="read_genesis",
        success=True,
        gaian_id=home.gaian_id,
        data=data,
        path=str(path),
    )


async def _write_genesis(
    home: GAIANHome, caller_id: str, data: Dict[str, Any], **_: Any
) -> FSToolResult:
    path = home.genesis_file
    _check_permission(caller_id, path)
    home.save_genesis(data)  # raises PermissionError if already exists (write-once)
    return FSToolResult(
        tool_name="write_genesis",
        success=True,
        gaian_id=home.gaian_id,
        path=str(path),
    )


async def _read_waveform(
    home: GAIANHome, caller_id: str, **_: Any
) -> FSToolResult:
    path = home.waveform_file
    _check_permission(caller_id, path)
    data = home.load_waveform()
    return FSToolResult(
        tool_name="read_waveform",
        success=True,
        gaian_id=home.gaian_id,
        data=data,
        path=str(path),
    )


async def _write_waveform(
    home: GAIANHome, caller_id: str, data: Dict[str, Any], **_: Any
) -> FSToolResult:
    path = home.waveform_file
    _check_permission(caller_id, path)
    home.save_waveform(data)
    return FSToolResult(
        tool_name="write_waveform",
        success=True,
        gaian_id=home.gaian_id,
        path=str(path),
    )


async def _read_memory_snapshot(
    home: GAIANHome, caller_id: str, **_: Any
) -> FSToolResult:
    path = home.memory_snapshot
    _check_permission(caller_id, path)
    data = home.load_memory_snapshot()
    return FSToolResult(
        tool_name="read_memory_snapshot",
        success=True,
        gaian_id=home.gaian_id,
        data=data,
        path=str(path),
    )


async def _write_memory_snapshot(
    home: GAIANHome, caller_id: str, data: Dict[str, Any], **_: Any
) -> FSToolResult:
    path = home.memory_snapshot
    _check_permission(caller_id, path)
    home.save_memory_snapshot(data)
    return FSToolResult(
        tool_name="write_memory_snapshot",
        success=True,
        gaian_id=home.gaian_id,
        path=str(path),
    )


async def _read_epoch(
    home: GAIANHome, caller_id: str, epoch_number: int = 0, **_: Any
) -> FSToolResult:
    path = home.epoch_file(epoch_number)
    _check_permission(caller_id, path)
    data = home.load_epoch(epoch_number)
    return FSToolResult(
        tool_name="read_epoch",
        success=True,
        gaian_id=home.gaian_id,
        data=data,
        path=str(path),
    )


async def _write_epoch(
    home: GAIANHome, caller_id: str,
    epoch_number: int = 0, data: Optional[Dict[str, Any]] = None,
    **_: Any
) -> FSToolResult:
    path = home.epoch_file(epoch_number)
    _check_permission(caller_id, path)
    home.save_epoch(epoch_number, data or {})
    return FSToolResult(
        tool_name="write_epoch",
        success=True,
        gaian_id=home.gaian_id,
        path=str(path),
    )


async def _write_session(
    home: GAIANHome, caller_id: str,
    session_id: str = "", data: Optional[Dict[str, Any]] = None,
    **_: Any
) -> FSToolResult:
    path = home.session_file(session_id)
    _check_permission(caller_id, path)
    home.save_session(session_id, data or {})
    return FSToolResult(
        tool_name="write_session",
        success=True,
        gaian_id=home.gaian_id,
        path=str(path),
    )


async def _read_home_stats(
    home: GAIANHome, caller_id: str, **_: Any
) -> FSToolResult:
    # Stats are non-sensitive — owner or gaia may read
    if caller_id != home.gaian_id and caller_id != "gaia":
        raise FSPermissionError(
            caller_id,
            home.identity_file,  # proxy for the home itself
            FSPermission.GAIA_READ,
        )
    return FSToolResult(
        tool_name="read_home_stats",
        success=True,
        gaian_id=home.gaian_id,
        data={
            "size_bytes": home.home_size_bytes(),
            "files": home.list_files(),
            "manifest_tampered": home.manifest.tampered_files,
        },
    )


async def _verify_integrity(
    home: GAIANHome, caller_id: str, **_: Any
) -> FSToolResult:
    if caller_id != home.gaian_id and caller_id != "gaia":
        raise FSPermissionError(
            caller_id,
            home.identity_file,
            FSPermission.GAIA_READ,
        )
    issues = home.verify_integrity()
    return FSToolResult(
        tool_name="verify_integrity",
        success=True,
        gaian_id=home.gaian_id,
        data={"issues": issues, "clean": len(issues) == 0},
    )


# ---------------------------------------------------------------------------
# Default tool set — ordered by priority
# ---------------------------------------------------------------------------

_DEFAULT_TOOLS: List[FSTool] = [
    # CRITICAL — system integrity and genesis
    FSTool(
        name="verify_integrity",
        description="Verify tamper-evident checksums for a GAIAN home directory.",
        priority=FSToolPriority.CRITICAL,
        is_write=False,
        handler=_verify_integrity,
    ),
    FSTool(
        name="read_genesis",
        description="Read the immutable GenesisRecord for a GAIAN.",
        priority=FSToolPriority.CRITICAL,
        is_write=False,
        handler=_read_genesis,
    ),
    FSTool(
        name="write_genesis",
        description="Write the GenesisRecord (write-once; raises if already exists).",
        priority=FSToolPriority.CRITICAL,
        is_write=True,
        handler=_write_genesis,
    ),
    # HIGH — identity, waveform, memory snapshot
    FSTool(
        name="read_identity",
        description="Read the GAIANIdentity snapshot.",
        priority=FSToolPriority.HIGH,
        is_write=False,
        handler=_read_identity,
    ),
    FSTool(
        name="write_identity",
        description="Write the GAIANIdentity snapshot.",
        priority=FSToolPriority.HIGH,
        is_write=True,
        handler=_write_identity,
    ),
    FSTool(
        name="read_waveform",
        description="Read the WaveformAvatar state.",
        priority=FSToolPriority.HIGH,
        is_write=False,
        handler=_read_waveform,
    ),
    FSTool(
        name="write_waveform",
        description="Write the WaveformAvatar state.",
        priority=FSToolPriority.HIGH,
        is_write=True,
        handler=_write_waveform,
    ),
    FSTool(
        name="read_memory_snapshot",
        description="Read the lifetime memory snapshot.",
        priority=FSToolPriority.HIGH,
        is_write=False,
        handler=_read_memory_snapshot,
    ),
    FSTool(
        name="write_memory_snapshot",
        description="Write the lifetime memory snapshot.",
        priority=FSToolPriority.HIGH,
        is_write=True,
        handler=_write_memory_snapshot,
    ),
    # NORMAL — epoch archives and sessions
    FSTool(
        name="read_epoch",
        description="Read a memory epoch archive by epoch number.",
        priority=FSToolPriority.NORMAL,
        is_write=False,
        handler=_read_epoch,
    ),
    FSTool(
        name="write_epoch",
        description="Write a memory epoch archive.",
        priority=FSToolPriority.NORMAL,
        is_write=True,
        handler=_write_epoch,
    ),
    FSTool(
        name="write_session",
        description="Write a session log entry.",
        priority=FSToolPriority.NORMAL,
        is_write=True,
        handler=_write_session,
    ),
    # LOW — introspection and stats
    FSTool(
        name="read_home_stats",
        description="Read home directory size and file listing.",
        priority=FSToolPriority.LOW,
        is_write=False,
        handler=_read_home_stats,
    ),
]


# ---------------------------------------------------------------------------
# FSToolRegistry
# ---------------------------------------------------------------------------

class FSToolRegistry:
    """
    Registers and dispatches filesystem tools for the agentic loop.

    Tools are stored in a dict keyed by name and sorted by priority
    for bulk operations. The registry is bound to a GAIAFilesystem
    instance and resolves GAIANHome objects on demand.

    Usage:
        registry = FSToolRegistry(fs=GAIAFilesystem())

        # Single dispatch
        result = await registry.execute(
            "read_identity", gaian_id="g-001", caller_id="g-001"
        )

        # Bulk priority-ordered dispatch
        results = await registry.execute_priority_batch(
            gaian_id="g-001", caller_id="gaia",
            tool_names=["verify_integrity", "read_genesis", "read_identity"]
        )

        # Introspect available tools
        tools = registry.list_tools(priority=FSToolPriority.HIGH)
    """

    def __init__(
        self,
        fs: GAIAFilesystem,
        extra_tools: Optional[List[FSTool]] = None,
    ) -> None:
        self._fs = fs
        self._tools: Dict[str, FSTool] = {}
        for tool in _DEFAULT_TOOLS:
            self._register(tool)
        for tool in (extra_tools or []):
            self._register(tool)

    def _register(self, tool: FSTool) -> None:
        if tool.name in self._tools:
            raise ValueError(
                f"FSToolRegistry: duplicate tool name {tool.name!r}. "
                f"Rename the tool or unregister the existing one first."
            )
        self._tools[tool.name] = tool

    def register(self, tool: FSTool) -> None:
        """Register a custom tool at runtime."""
        self._register(tool)

    def unregister(self, name: str) -> None:
        """Remove a tool from the registry."""
        self._tools.pop(name, None)

    def get(self, name: str) -> Optional[FSTool]:
        """Return a tool by name, or None if not registered."""
        return self._tools.get(name)

    def list_tools(
        self,
        priority: Optional[FSToolPriority] = None,
        is_write: Optional[bool] = None,
    ) -> List[FSTool]:
        """
        List registered tools, optionally filtered by priority or read/write.
        Results are sorted by priority (CRITICAL first).
        """
        tools = list(self._tools.values())
        if priority is not None:
            tools = [t for t in tools if t.priority == priority]
        if is_write is not None:
            tools = [t for t in tools if t.is_write == is_write]
        return sorted(tools, key=lambda t: t.priority)

    async def execute(
        self,
        tool_name: str,
        gaian_id: str,
        caller_id: Optional[str] = None,
        **kwargs: Any,
    ) -> FSToolResult:
        """
        Execute a single tool by name.

        Args:
            tool_name  : Registered tool name.
            gaian_id   : The GAIAN whose home will be acted on.
            caller_id  : The GAIAN making the request (defaults to gaian_id).
            **kwargs   : Tool-specific arguments (e.g. data=, epoch_number=).

        Returns:
            FSToolResult — always; never raises.
        """
        effective_caller = caller_id or gaian_id
        tool = self._tools.get(tool_name)
        if tool is None:
            return FSToolResult(
                tool_name=tool_name,
                success=False,
                gaian_id=effective_caller,
                error=f"No tool registered with name {tool_name!r}.",
                error_type="ToolNotFound",
            )
        home = self._fs.gaian_home(gaian_id)
        return await tool.execute(home=home, caller_id=effective_caller, **kwargs)

    async def execute_priority_batch(
        self,
        gaian_id: str,
        tool_names: List[str],
        caller_id: Optional[str] = None,
        concurrency: int = 4,
        **kwargs: Any,
    ) -> List[FSToolResult]:
        """
        Execute multiple tools in priority order with bounded concurrency.

        Tools with the same priority level run concurrently up to
        `concurrency` at a time. Tools at higher priority levels
        complete before lower-priority ones begin.

        Args:
            gaian_id    : GAIAN whose home is acted on.
            tool_names  : List of tool names to execute.
            caller_id   : Caller identity (defaults to gaian_id).
            concurrency : Max concurrent tasks per priority level.
            **kwargs    : Passed to every tool in the batch.

        Returns:
            List[FSToolResult] in priority-then-input order.
        """
        effective_caller = caller_id or gaian_id
        home = self._fs.gaian_home(gaian_id)

        # Group tools by priority, preserving input order within each group
        by_priority: Dict[int, List[FSTool]] = {}
        unknown_results: List[FSToolResult] = []

        for name in tool_names:
            tool = self._tools.get(name)
            if tool is None:
                unknown_results.append(FSToolResult(
                    tool_name=name,
                    success=False,
                    gaian_id=effective_caller,
                    error=f"No tool registered with name {name!r}.",
                    error_type="ToolNotFound",
                ))
            else:
                by_priority.setdefault(tool.priority, []).append(tool)

        results: List[FSToolResult] = []

        for priority_level in sorted(by_priority):
            tools_at_level = by_priority[priority_level]
            semaphore = asyncio.Semaphore(concurrency)

            async def _run(t: FSTool) -> FSToolResult:
                async with semaphore:
                    return await t.execute(
                        home=home, caller_id=effective_caller, **kwargs
                    )

            level_results = await asyncio.gather(
                *[_run(t) for t in tools_at_level]
            )
            results.extend(level_results)

        results.extend(unknown_results)
        return results

    def __repr__(self) -> str:
        return (
            f"FSToolRegistry("
            f"tools={len(self._tools)}, "
            f"fs_root={self._fs.root})"
        )
