---
title: "[G-7] Live Dev Suite Watcher — File Watch, Auto-Reload & Test Trigger"
labels: ["enhancement", "dev-suite", "sprint:G-7", "priority:medium"]
---

## Overview

The GAIA-OS Dev Suite currently requires manual action to reload files and re-run tests. Any modern developer experience — and any agentic coding assistant — benefits from live feedback: the editor auto-refreshes when a file changes on disk, tests run on save, and linting results appear inline without a button press.

The Live Dev Suite Watcher uses the Tauri FS plugin's built-in `watch` / `watchImmediate` APIs to make the Dev Suite reactive to disk changes. It also provides the foundation for the Bug Capture module: a single action that captures the current editor state + recent watch events + recent logs as a structured bug report bundle.

## Background & Motivation

The Tauri v2 FS plugin ships with file watching built in — `watch()` (debounced) and `watchImmediate()` (immediate) are first-class APIs that emit structured events into the webview. Recursive watching is supported with `{ recursive: true }`. This means the watcher can be implemented without any native sidecar code — it is purely a Tauri TypeScript module consuming an existing API.

This is a high-leverage, low-risk module: it consumes a stable Tauri API, does not require new dependencies, and immediately improves the developer experience while laying infrastructure for the Research Desk ingestion pipeline in G-10.

## Architecture

```
src/
  services/
    filesystem/
      watcher.ts           # WatchService (shared with WorkspaceService #G7-006)
  dev-suite/
    watcher-integration.ts # DevSuiteWatcher — binds WatchService to Dev Suite actions
    watch-config.ts        # WatchConfig: roots, debounce, triggers
    bug-capture.ts         # BugCapture — snapshot of editor + events + logs
```

### WatchConfig

```typescript
interface WatchConfig {
  roots: GaiaPath[];           // Directories to watch (from WorkspaceService)
  recursive: boolean;          // Default: true for project roots
  debounceMs: number;          // Default: 300 ms
  triggers: WatchTrigger[];    // What to do on change
}

type WatchTrigger =
  | { type: 'reload_editor'; filePattern: string }
  | { type: 'run_tests'; command: string }
  | { type: 'run_lint'; command: string }
  | { type: 'run_format'; command: string }
  | { type: 'notify_ui'; message: string };
```

### Bug Capture bundle

When the user clicks **Report Bug** in the Dev Suite, `BugCapture.capture()` assembles:

```typescript
interface BugCaptureBundle {
  timestamp: string;
  correlation_id: string;
  editor_state: {
    open_files: string[];       // File paths (not contents)
    active_file: string;
    cursor_position: { line: number; col: number };
  };
  recent_watch_events: WatchEvent[];   // Last 20 events
  recent_logs: string[];               // Last 50 log lines (sanitized)
  screenshot_path: string | null;      // Optional — from Vision Capture
  platform: string;
  gaia_version: string;
}
```

The bundle is saved to `$APPLOG/gaia/bug_captures/` and a GitHub issue draft is pre-filled with its summary.

## Acceptance Criteria

- [ ] `WatchService` watches the active Dev Suite project root with `{ recursive: true }` and the configured debounce.
- [ ] File changes trigger the correct `WatchTrigger` actions (reload, test, lint, format) based on `WatchConfig`.
- [ ] Watch events are debounced — no trigger fires more than once per debounce window for the same file.
- [ ] `BugCapture.capture()` produces a complete, sanitized `BugCaptureBundle` in under 500 ms.
- [ ] Bug capture bundles are saved to `$APPLOG/gaia/bug_captures/` using `WorkspaceService`.
- [ ] No raw file contents or secrets are stored in bug capture bundles.
- [ ] Watchers are properly cleaned up (`.stop()`) when the Dev Suite project is closed.
- [ ] Unit tests cover: trigger dispatch, debounce behavior, bundle sanitization, watcher cleanup.

## Dependencies

- `@tauri-apps/plugin-fs` v2 — watch/watchImmediate APIs
- `WorkspaceService` / `WatchService` (#G7-006)
- Execution Sandbox Service (#G7-001) — test/lint/format triggers run through the sandbox
- `core/logger.py` — log lines for bug capture bundle

## Cross-References

- Sprint G-7: Workspace Service (#G7-006)
- Sprint G-10: Research Desk ingestion (watch on Download folder)
- Sprint G-11: Vision Capture Panel (optional screenshot attachment in bug bundles)
- Tauri FS plugin docs: https://v2.tauri.app/plugin/file-system/#watching-changes

## Labels
`enhancement` `dev-suite` `sprint:G-7` `priority:medium`

## Priority
🟡 Medium — high leverage for developer experience; low implementation risk.
