"""
GAIA Filesystem Abstraction.

Every GAIAN has a sovereign home directory on the device — a place
that belongs to them. It is not a cache, not a config folder, not
a data directory. It is a home.

The filesystem abstraction provides:
  1. GAIA_ROOT          — the root directory for all GAIA data
  2. GAIANHome          — the sovereign home directory for one GAIAN
  3. GAIAFSManifest     — the tamper-evident directory manifest
  4. GAIAFilesystem     — the top-level filesystem manager

The tools layer (tools.py) provides:
  5. FSToolPriority     — CRITICAL / HIGH / NORMAL / LOW priority enum
  6. FSToolResult       — uniform result envelope (never raises into agentic loop)
  7. FSTool             — named, prioritized, async-ready tool wrapper
  8. FSToolRegistry     — registers and dispatches tools by priority
  9. FSPermissionError  — raised (then captured) on permission violations

Directory structure:
  <gaia_root>/
    .gaia/                     — GAIA's own sovereign data
      memory/                  — GAIA sovereign memory snapshots
      manifests/               — boot manifests
      config.json              — GAIA system configuration
    gaians/
      <gaian_id>/              — each GAIAN's home
        .home                  — home manifest (tamper-evident)
        identity/
          identity.json        — GAIANIdentity snapshot
          genesis.json         — GenesisRecord (sealed, read-only)
          autonomy.json        — AutonomyRecord
        memory/
          lifetime.snap        — encrypted lifetime memory snapshot
          epochs/              — consolidated epoch archives
        avatar/
          waveform.json        — WaveformAvatar state
          evolution.json       — avatar evolution log
        sessions/              — session logs (pruned on schedule)

Design principles:
  - OFFLINE-FIRST: All reads/writes are local. Cloud sync is
    a separate, optional, always-encrypted layer above this.
  - TAMPER-EVIDENT: Every home directory has a manifest with
    checksums. GAIA detects tampering at every boot.
  - CROSS-PLATFORM: Paths are resolved using pathlib. The
    abstraction works on Linux, macOS, and Windows.
  - SOVEREIGN: A GAIAN's home is theirs. The filesystem layer
    enforces that no GAIAN can read another's home without
    explicit, logged consent.
  - PRIORITY-DISPATCHED: The agentic loop consumes tools via
    FSToolRegistry, which executes CRITICAL tools first, captures
    all errors as FSToolResult, and supports concurrent batching.
"""
from core.fs.filesystem import (
    GAIAPath,
    GAIANHome,
    GAIAFSManifest,
    GAIAFilesystem,
    FSPermission,
)
from core.fs.tools import (
    FSToolPriority,
    FSToolResult,
    FSTool,
    FSToolRegistry,
    FSPermissionError,
)

__all__ = [
    # filesystem.py
    "GAIAPath",
    "GAIANHome",
    "GAIAFSManifest",
    "GAIAFilesystem",
    "FSPermission",
    # tools.py
    "FSToolPriority",
    "FSToolResult",
    "FSTool",
    "FSToolRegistry",
    "FSPermissionError",
]
