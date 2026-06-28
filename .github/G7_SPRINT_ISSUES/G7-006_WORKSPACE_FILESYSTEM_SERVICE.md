---
title: "[G-7] Workspace & Filesystem Service — Tauri FS Plugin Abstraction for GAIA-OS"
labels: ["enhancement", "platform", "sprint:G-7", "priority:medium"]
---

## Overview

GAIA-OS performs filesystem operations in multiple subsystems — Dev Suite, Crystal exports/imports, settings persistence, research ingestion, and future audit log paths — but these operations are scattered, use inconsistent path resolution, and bypass the Tauri file system plugin's capability and permission system. On mobile platforms, this will fail silently or break outright.

The Workspace & Filesystem Service wraps the Tauri FS plugin (`@tauri-apps/plugin-fs`) into a single, GAIA-aware service layer. Every filesystem operation in GAIA flows through this service, which enforces base-directory scoping, capability declarations, and cross-platform path resolution.

## Background & Motivation

The Tauri v2 filesystem plugin prevents path traversal attacks, requires explicit capabilities for each access scope, and handles the per-platform access restrictions (Android/iOS restrict to application folders; macOS/Linux deny `$RESOURCES` writes). It also provides file watching with debounced and immediate modes, recursive directory listing, metadata access, and atomic copy/rename operations.

By wrapping this behind a service layer, GAIA gains:
- A single point for capability declarations (declared once in `capabilities/`, consumed everywhere).
- Cross-platform correct path resolution using base directories (`$APPDATA`, `$APPLOCALDATA`, `$APPLOG`, `$DOCUMENT`, etc.).
- A foundation for the Live Dev Suite Watcher (#G7-007) and Research Desk ingestion pipeline (G-10).

## Architecture

### Tauri side (TypeScript)

```
src/
  services/
    filesystem/
      index.ts             # WorkspaceService — public API
      paths.ts             # GaiaPath enum + resolve() helper
      watcher.ts           # WatchService — wraps fs.watch / fs.watchImmediate
      permissions.ts       # Capability assertion helpers
```

### Core side (Python, for sidecar/service layer)

```
core/
  workspace/
    __init__.py
    workspace_service.py   # WorkspaceService — open/read/write/list/watch project paths
    gaia_paths.py          # Canonical path registry (maps to Tauri base dirs via env vars)
    project.py             # Project dataclass: root, name, language, active files
```

### GaiaPath enum

```typescript
enum GaiaPath {
  AppData       = 'AppData',       // Settings, persona state, registry
  AppLocalData  = 'AppLocalData',  // Audit DB, model registry
  AppLog        = 'AppLog',        // Execution audit JSONL, app logs
  AppCache      = 'AppCache',      // Temporary build artifacts
  Document      = 'Document',      // User-opened project roots
  Download      = 'Download',      // Research ingestion watch root (default)
  Picture       = 'Picture',       // Vision Capture outputs
}
```

### Capability declarations

All required FS capabilities must be declared in `src-tauri/capabilities/gaia-fs.json`:

```json
{
  "identifier": "gaia-fs",
  "permissions": [
    "fs:allow-app-read-recursive",
    "fs:allow-app-write-recursive",
    "fs:allow-applog-write-recursive",
    "fs:allow-applocaldata-read-recursive",
    "fs:allow-applocaldata-write-recursive",
    "fs:allow-document-read",
    "fs:allow-download-read"
  ]
}
```

## Acceptance Criteria

- [ ] `WorkspaceService` is the sole entry point for all filesystem operations in the Tauri frontend.
- [ ] All base-directory paths are resolved using the Tauri FS plugin's base directory system — no raw absolute paths in application code.
- [ ] The capability file `gaia-fs.json` declares exactly the permissions GAIA needs, no more.
- [ ] Path traversal is tested: attempts to access `../` paths are rejected.
- [ ] File watching is abstracted behind `WatchService.watch(path, handler, { recursive })` with correct debounce defaults.
- [ ] Dev Suite file I/O is migrated to use `WorkspaceService`.
- [ ] Crystal export/import uses `WorkspaceService` with `GaiaPath.Document`.
- [ ] Unit tests cover: base-dir resolution for all `GaiaPath` values, path traversal rejection, watcher event delivery.

## Dependencies

- `@tauri-apps/plugin-fs` v2 — https://v2.tauri.app/plugin/file-system/
- Tauri capabilities system
- Dev Suite (consumer)
- Crystal services (consumer)
- Audit Log Normalizer (#G7-004) — uses `GaiaPath.AppLog` and `GaiaPath.AppLocalData`

## Cross-References

- Sprint G-7: Audit Log Normalizer (#G7-004)
- Sprint G-10: Research Desk ingestion pipeline (uses `GaiaPath.Download` watch root)
- Tauri FS plugin docs: https://v2.tauri.app/plugin/file-system/

## Labels
`enhancement` `platform` `sprint:G-7` `priority:medium`

## Priority
🟡 Medium — required before G-10 Research Desk and before mobile portability work in G-12.
