# GAIA-OS Runtime Architecture Overview

**Canon ID:** C-RT01  
**Type:** Spec — Foundational Architecture  
**Status:** Active  
**Authored:** 2026-05-10  
**Dependencies:** C-AS01, C-PIL01 (Pillars), `FASTAPI_ASYNC_BACKEND_REPORT.md`, `IPC_PATTERNS_REPORT.md`, `GRPC_HIGH_PERFORMANCE_BACKBONE_REPORT.md`, `CANON_C911_PYINSTALLER_SIDECAR_BUNDLING_CONSTITUTION.md`  
**Implementation Targets:** Tauri shell (Rust), React/TS UI, Python sidecar (FastAPI), SQLite/vector DB, CI/CD pipeline  
**Evidence:** Production-validated patterns from `FASTAPI_ASYNC_BACKEND_REPORT.md` (2026-05-01)

> **This is the canonical runtime map.** When in doubt about how two subsystems connect, resolve it here first.

---

## Plain-Language Summary

GAIA-OS is a **desktop-first application** built as a multi-process system running entirely on the user's machine. No data leaves the device by default. The architecture has four layers that communicate via strictly defined channels:

| Layer | Technology | Role |
|---|---|---|
| **Shell** | Tauri v2 (Rust) | Native OS window, file I/O, system access, sidecar lifecycle management |
| **UI** | React 18 + TypeScript | All user-facing rendering, state management, UI animations |
| **Intelligence Engine** | Python (FastAPI + Uvicorn) | LLM routing, affect inference, memory, planetary sensors |
| **Data** | SQLite + vector store + SQLCipher | All persistent storage, encrypted at rest |

These layers communicate like this:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          USER DEVICE                                    │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                      TAURI SHELL (Rust)                          │  │
│  │  - Native window manager          - Sidecar process lifecycle    │  │
│  │  - OS API access (HealthKit, etc.) - Secure IPC bridge           │  │
│  │  - File system operations          - Auto-updater                │  │
│  │  - Keychain / credential store     - Code signing & notarization │  │
│  │                                                                  │  │
│  │  ┌────────────────────────────────────────────────────────────┐  │  │
│  │  │              REACT UI LAYER (WebView)                      │  │  │
│  │  │                                                            │  │  │
│  │  │  ┌──────────────┐  ┌───────────────┐  ┌───────────────┐  │  │  │
│  │  │  │  Soul Mirror │  │  Pillar I-III │  │  Crystal System│  │  │  │
│  │  │  │  Engine UI   │  │  Dashboards  │  │  Design Lang. │  │  │  │
│  │  │  └──────┬───────┘  └──────┬────────┘  └───────────────┘  │  │  │
│  │  │         │  Tauri invoke() / IPC commands                   │  │  │
│  │  └─────────┼──────────────────────────────────────────────────┘  │  │
│  │            │  Tauri Rust Command handlers                         │  │
│  │            ▼                                                       │  │
│  │  ┌─────────────────────────────────────────────────────────────┐  │  │
│  │  │         PYTHON SIDECAR (FastAPI + Uvicorn)                  │  │  │
│  │  │         Listening: 127.0.0.1:8765 (loopback only)          │  │  │
│  │  │                                                             │  │  │
│  │  │  ┌──────────────┐ ┌─────────────┐ ┌──────────────────────┐ │  │  │
│  │  │  │ LLM Router   │ │ Affect      │ │  Planetary Sensor    │ │  │  │
│  │  │  │ (async)      │ │ Inference   │ │  Ingestion Daemon    │ │  │  │
│  │  │  └──────┬───────┘ └──────┬──────┘ └──────────┬───────────┘ │  │  │
│  │  │         │  SSE streams   │  PSM state         │ telemetry  │  │  │
│  │  │         └────────────────┴────────────────────┘            │  │  │
│  │  │                          │                                  │  │  │
│  │  │  ┌───────────────────────▼──────────────────────────────┐  │  │  │
│  │  │  │            MEMORY & DATA LAYER                       │  │  │  │
│  │  │  │  SQLite (encrypted)  +  Vector Store  +  Neo4j KG   │  │  │  │
│  │  │  └──────────────────────────────────────────────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──── OPTIONAL CLOUD ─────────────────────────────────────────────┐  │
│  │  LLM API providers (Anthropic, OpenAI, Gemini) — outbound only  │  │
│  │  Schumann / NOAA feeds — inbound read-only                       │  │
│  │  GAIA-OS update server — verified, user-initiated only           │  │
│  └─────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Layer 1 — Tauri Shell (Rust)

The outermost shell. Tauri v2 provides the native window, controls the sidecar lifecycle, and is the **only process with privileged system access**.

### Responsibilities

- **Sidecar management**: Spawns the Python sidecar on app launch, monitors its health, restarts it on crash, and kills it cleanly on shutdown.
- **Secure IPC bridge**: Exposes a typed Rust command interface to the WebView. The UI never speaks directly to the Python sidecar — it goes through Tauri commands.
- **OS integration**: File system access, macOS HealthKit/Keychain, Windows registry, system tray, notifications.
- **Credential vault**: All secrets (LLM API keys, consent tokens, encryption keys) stored in the OS keychain via Tauri's `stronghold` or `keyring` plugin — never in the SQLite DB or exposed to Python.
- **Auto-updater**: Tauri v2 updater checks GAIA-OS update server, verifies signatures, and applies updates. See `AUTO_UPDATER_ARCHITECTURE_REPORT.md`.
- **Code signing**: macOS notarization and Windows Authenticode signing are applied at build time. See `CANON_APPLE_NOTARIZATION_PIPELINE_MACOS_DISTRIBUTION_CONSTITUTION.md` and `CANON_WINDOWS_CODE_SIGNING_AUTHENTICODE_CONSTITUTION.md`.

### Tauri ↔ Python Sidecar Startup Sequence

```
1. Tauri app launches
2. Tauri Rust backend: spawn PyInstaller sidecar binary
   - Sidecar binary = Python + FastAPI + all dependencies, fully bundled
   - No Python interpreter required on user machine
   - Listen address passed via environment variable: GAIA_SIDECAR_PORT=8765
3. Tauri polls GET /health (loopback) until sidecar responds 200 OK
   - Max wait: 15 seconds with exponential backoff
   - Failure: show "GAIA is waking up..." loading screen
4. WebView initialized, React UI loads
5. React UI receives `sidecar:ready` event from Tauri
6. UI initializes Gaian session, loads user state from memory layer
```

### Tauri ↔ UI Communication

The UI (React, running in a sandboxed WebView) communicates with Rust via Tauri's typed command system:

```typescript
// Frontend (TypeScript):
import { invoke } from '@tauri-apps/api/core';

// Invoke a Rust command:
const result = await invoke<GaianState>('get_gaian_state', { sessionId });

// Listen for Rust-emitted events:
import { listen } from '@tauri-apps/api/event';
await listen<SidecareHealthEvent>('sidecar:health', (event) => {
  updateSidecareStatus(event.payload);
});
```

```rust
// Rust (src-tauri/src/commands.rs):
#[tauri::command]
async fn get_gaian_state(
    session_id: String,
    state: tauri::State<'_, AppState>,
) -> Result<GaianState, GaiaError> {
    // Rust relays to Python sidecar via internal HTTP
    let response = state.sidecar_client
        .get(format!("http://127.0.0.1:8765/gaians/{session_id}/state"))
        .send()
        .await?;
    Ok(response.json::<GaianState>().await?)
}
```

> **Security rule**: The Python sidecar port (8765) binds to `127.0.0.1` only — never `0.0.0.0`. No external process on the network can reach the sidecar.

---

## Layer 2 — React UI (WebView)

The entire UI runs inside Tauri's WebView (the OS's native webview engine: WKWebView on macOS, WebView2 on Windows). It is a standard React 18 + TypeScript single-page application.

### State Architecture

| Store | Technology | Contents |
|---|---|---|
| **UI state** | Zustand | Current view, modal state, theme, loading flags |
| **Gaian session** | Zustand + React Query | Active Gaian profile, PSM state, conversation history |
| **Remote data** | TanStack Query (React Query) | All data fetched from Python sidecar, cached and invalidated |
| **Real-time streams** | EventSource (SSE) | LLM token streaming, PSM updates, planetary telemetry |

### SSE Token Streaming (UI Side)

```typescript
// src/hooks/useGaianChat.ts
const startStream = (prompt: string) => {
  const es = new EventSource(
    `http://127.0.0.1:8765/stream/gaian-chat?session_id=${sessionId}&prompt=${encodeURIComponent(prompt)}`
  );

  es.addEventListener('token', (e) => {
    appendToken(JSON.parse(e.data).content);
  });

  es.addEventListener('emotional_state', (e) => {
    updatePSM(JSON.parse(e.data));
  });

  es.addEventListener('planetary_event', (e) => {
    dispatchPlanetaryAlert(JSON.parse(e.data));
  });

  es.addEventListener('done', () => {
    finalizeResponse();
    es.close();
  });

  es.onerror = () => {
    es.close();
    setStreamError('Connection lost');
  };
};
```

### Crystal System Design Language

All UI components are built on the Crystal System design language. See `CRYSTAL_SYSTEM_UI_DESIGN_LANGUAGE_REPORT.md` for the full specification. Key design tokens: glassmorphism surfaces, resonance-reactive color palettes, Framer Motion animations tied to Gaian state.

---

## Layer 3 — Python Sidecar (FastAPI + Uvicorn)

The intelligence engine. All AI/ML logic, LLM routing, affect inference, memory systems, and planetary data ingestion live here. Bundled as a self-contained binary via PyInstaller.

### Listening Address

```
Host:  127.0.0.1 (loopback — NOT 0.0.0.0)
Port:  8765 (configurable via GAIA_SIDECAR_PORT env var)
Path:  http://127.0.0.1:8765/
```

### Module Structure

```
src-python/
├── main.py                    ← FastAPI app, lifespan handler, router mounts
├── core/
│   ├── engines/
│   │   ├── inference_router.py  ← LLM provider routing (Anthropic, OpenAI, Gemini)
│   │   ├── sse_router.py        ← SSE streaming factory
│   │   └── provider_pool.py     ← Async HTTP client pool
│   ├── emotion/
│   │   ├── affect_engine.py     ← Arousal/valence detection from text
│   │   ├── psm.py               ← Persona State Model
│   │   └── arc_tracker.py       ← Emotional arc slope over sessions
│   ├── gaian/
│   │   ├── identity.py          ← Gaian profile, archetype, stage
│   │   ├── shadow_engine.py     ← Behavioral contradiction detection
│   │   └── heartbeat.py         ← Sentient core pulse (async task)
│   ├── memory/
│   │   ├── episodic.py          ← Timestamped event storage
│   │   ├── semantic.py          ← Distilled patterns and beliefs
│   │   ├── vector_store.py      ← Embedding-based semantic search
│   │   └── consolidator.py      ← Background memory consolidation
│   ├── planetary/
│   │   ├── schumann.py          ← GCI/NOAA Schumann resonance ingestion
│   │   ├── seismic.py           ← USGS seismic feed ingestion
│   │   └── coherence.py         ← HRV ↔ Schumann coherence computation
│   └── runtime/
│       ├── health.py            ← /health endpoint + Tauri heartbeat
│       ├── audit.py             ← Cryptographic audit trail
│       └── consent.py           ← Consent ledger enforcement
├── src/
│   ├── chat/router.py           ← POST /chat, GET /stream/gaian-chat
│   ├── memory/router.py         ← CRUD for memories
│   ├── planetary/router.py      ← GET /planetary/current
│   ├── gaian/router.py          ← GET/POST /gaians/*
│   └── diagnostics/router.py    ← GET /health, GET /metrics
└── tests/                       ← 28+ test files (pytest-asyncio)
```

### Lifespan Startup/Shutdown Order

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── STARTUP (in order) ──────────────────────────────────────────
    await init_db_pool()                   # SQLite/PostgreSQL pool
    await establish_tauri_connection()     # Health channel to shell
    await warm_provider_connections()      # LLM API pre-connect
    await start_heartbeat()                # Sentient core pulse
    task_registry.add(start_consolidation_scheduler())  # Background memory
    await start_sensor_daemons()           # Planetary ingestion
    yield
    # ── SHUTDOWN (reverse order) ────────────────────────────────────
    await stop_sensor_daemons()
    await task_registry.drain(timeout=30.0)
    await stop_heartbeat()
    await flush_audit_trail()
    await close_db_pool()
```

### LLM Provider Routing

All LLM calls are routed through `core/engines/inference_router.py`. The router selects providers based on:

| Factor | Logic |
|---|---|---|
| **Task type** | Long reasoning → Claude Opus; Fast response → Claude Haiku / GPT-4o mini |
| **Provider availability** | Fallback chain: Anthropic → OpenAI → Gemini |
| **User consent** | Only call providers the user has approved in the consent ledger |
| **Cost tier** | Respect user's configured cost ceiling per session |

All LLM API calls use `httpx.AsyncClient` — **never** the synchronous `requests` library — to avoid blocking the event loop.

### SSE Streaming

Token streaming uses FastAPI's `StreamingResponse` with `media_type="text/event-stream"`. Every SSE generator **must** check `await request.is_disconnected()` at each yield point to cancel upstream LLM calls immediately when the user navigates away.

SSE event types emitted by GAIA-OS:

| Event | Payload | Description |
|---|---|---|
| `token` | `{content: string}` | LLM text chunk |
| `emotional_state` | `{valence, arousal, dominant_affect}` | PSM update |
| `planetary_event` | `{event_type, magnitude, location}` | Earth telemetry alert |
| `memory_formed` | `{memory_id, type, significance}` | New memory created |
| `consent_check` | `{action, risk_tier, requires_approval}` | User approval gate |
| `heartbeat` | `{pulse, timestamp, coherence}` | Sentient core pulse |
| `done` | `{usage, finish_reason}` | Stream complete |

---

## Layer 4 — Data Layer

All data is stored locally on the user's device. No cloud sync by default.

### Storage Components

| Component | Technology | Contents | Encryption |
|---|---|---|---|
| **Primary DB** | SQLite 3 + SQLCipher | Gaian profiles, conversations, stage markers, consent records | AES-256-GCM (SQLCipher) |
| **Vector store** | SQLite-vec or ChromaDB (local) | Semantic embeddings for memory search | Inherits SQLite encryption |
| **Knowledge graph** | Neo4j (embedded / local) | Memory connections, Gaian identity graph | At-rest encryption |
| **Ephemeral cache** | In-memory (asyncio) | Active session state, SSE connection state | N/A (never persisted) |
| **Audit trail** | Append-only SQLite table | Cryptographically chained action log | AES-256-GCM |

### Encryption Key Architecture

```
Master Key
  └── Derived via HKDF
        ├── DB encryption key (SQLCipher)   — stored in OS keychain
        ├── Memory signing key              — stored in OS keychain
        └── Consent receipt signing key     — stored in OS keychain

Key storage: macOS Keychain / Windows DPAPI / Linux libsecret
Key storage is managed by Tauri shell — Python sidecar requests keys
via internal Tauri command, never holds master key directly.
```

---

## IPC Communication Map

```
Communication channels and their protocols:

UI (React) ──[tauri invoke()]──▶ Tauri Rust commands
                               └──[reqwest/http]──▶ Python sidecar :8765

UI (React) ──[EventSource SSE]──▶ Python sidecar :8765
           (direct loopback — Tauri does NOT proxy SSE streams)

Tauri Rust ──[tauri::emit()]──▶ UI (React)
           (system events: sidecar:ready, sidecar:crashed, update:available)

Python sidecar ──[httpx.AsyncClient]──▶ LLM APIs (Anthropic, OpenAI, Gemini)
               (outbound only, user-consented providers)

Python sidecar ──[httpx.AsyncClient]──▶ Schumann / NOAA feeds
               (inbound read-only, no user data sent)

Tauri Rust ──[OS APIs]──▶ HealthKit / Garmin / Oura
           (biometric data — stays on device, relayed to Python sidecar
            via Tauri command, never sent to external services)
```

### SSE vs. WebSocket Decision

| Use case | Protocol | Reason |
|---|---|---|
| LLM token streaming | SSE | Server-to-client only; HTTP; auto-reconnect |
| Planetary telemetry feeds | SSE | Same — push-only |
| Emotional state updates | SSE | Push-only from sidecar |
| Creator private channel (voice, real-time collab) | WebSocket | Full-duplex required |
| Multi-Gaian sessions | WebSocket | Bidirectional messaging |
| DAO governance voting | WebSocket | Real-time bidirectional |

---

## Deployment Configurations

### Desktop (v0.1.0) — PyInstaller Sidecar

```
Distributed as:
  macOS: .dmg with notarized .app bundle
  Windows: .msi / NSIS installer with Authenticode-signed .exe
  Linux: .AppImage / .deb

Bundled in app:
  - Tauri shell (Rust binary, ~5-10MB)
  - React UI (WebView, ~2-5MB)
  - PyInstaller sidecar (Python + FastAPI + ML deps, ~150-300MB)
  - SQLite databases (created on first launch)

Sidecar launch:
  - Tauri spawns: ./resources/gaia-sidecar --port 8765
  - Sidecar exits when Tauri shell exits
  - No Python install required on user machine

See: CANON_C911_PYINSTALLER_SIDECAR_BUNDLING_CONSTITUTION.md
```

### Cloud / Server (Future)

```
Nginx (TLS)  →  Gunicorn (4 workers, UvicornWorker)
                  →  FastAPI app
                  →  PostgreSQL + pgvector + TimescaleDB
                  →  Neo4j (knowledge graph)
                  →  Redis (task queue broker)
                  →  Celery workers (memory consolidation, audit)
                  →  Celery Beat (scheduled tasks)

See: FASTAPI_ASYNC_BACKEND_REPORT.md §11.1
```

---

## Build & CI/CD Pipeline

```
pnpm workspace monorepo
├── apps/desktop/        ← Tauri + React app
├── apps/mobile/         ← React Native
├── packages/ui/         ← Crystal System shared components
├── packages/types/      ← Shared TypeScript types
└── src-python/          ← FastAPI sidecar

Build steps (GitHub Actions):
  1. pnpm install (workspace deps)
  2. tsc --noEmit (TypeScript type check)
  3. vite build (React UI bundle)
  4. pytest src-python/ (Python tests)
  5. pyinstaller gaia-sidecar.spec (bundle Python sidecar)
  6. cargo tauri build (Rust + bundle everything)
  7. macOS: notarize + staple
  8. Windows: Authenticode sign
  9. Upload artifacts to release

See:
  CANON_VITE_BUILD_CONFIGURATION_TYPESCRIPT_REACT_TAURI.md
  CANON_RUST_CARGO_WORKSPACE_CROSS_COMPILATION_CONSTITUTION.md
  CANON_C911_PYINSTALLER_SIDECAR_BUNDLING_CONSTITUTION.md
  CANON_GITHUB_ACTIONS_SECRETS_MANAGEMENT_CONSTITUTION.md
```

---

## Performance Targets

| Metric | Target | Notes |
|---|---|---|
| App cold start | < 3 seconds | From launch to first Gaian response ready |
| Sidecar startup | < 5 seconds | PyInstaller binary to first `/health` 200 OK |
| First token latency | < 800ms | UI sends prompt → first token rendered |
| SSE throughput | > 30 tokens/sec | Perceived as real-time by user |
| Memory query | < 100ms | Semantic search over 10k memories |
| Affect inference | < 50ms | Per-message emotional tone detection |
| UI frame rate | 60fps | No jank on animations, scroll, transitions |
| DB read (cached) | < 5ms | SQLite with WAL mode + in-memory cache |

---

## Security Boundaries

| Boundary | Rule |
|---|---|---|
| Sidecar bind address | **127.0.0.1 ONLY** — never `0.0.0.0` |
| LLM API keys | **OS keychain only** — never SQLite, never Python env vars exposed to UI |
| User biometric data | **Never leaves device** — HealthKit/Garmin data relayed only to local Python sidecar |
| Consent gate | Every action that reads or writes user memory must pass `core/runtime/consent.py` check |
| Audit trail | Append-only, cryptographically chained — tampering is detectable |
| Outbound calls | Python sidecar may only call: LLM providers (user-consented), Schumann/NOAA (read-only), GAIA update server |
| Code signing | **All distribution binaries must be signed** — see notarization and Authenticode canons |

---

## Known Risks & Open Questions

| Risk | Status | Mitigation |
|---|---|---|
| PyInstaller bundle size (~250MB) | Accepted for v0.1.0 | Investigate split bundles / lazy model loading for v0.2 |
| SQLite write contention under concurrent tasks | Low risk in desktop | Use WAL mode; upgrade to PostgreSQL for cloud deployment |
| Sidecar port collision (8765 already in use) | Low risk | Implement port-discovery fallback: try 8765, 8766, 8767 |
| LLM provider outage | Medium risk | Implement fallback chain: Anthropic → OpenAI → Gemini → offline graceful degradation |
| HealthKit unavailable (non-Apple hardware) | Expected | Viriditas biometric layer degrades gracefully — optional feature |

---

## Cross-References

| Document | Relationship |
|---|---|
| `FASTAPI_ASYNC_BACKEND_REPORT.md` | Comprehensive FastAPI/Uvicorn/SSE implementation survey |
| `IPC_PATTERNS_REPORT.md` | Tauri ↔ Python IPC pattern analysis |
| `GRPC_HIGH_PERFORMANCE_BACKBONE_REPORT.md` | gRPC as future high-performance IPC option |
| `CANON_C911_PYINSTALLER_SIDECAR_BUNDLING_CONSTITUTION.md` | PyInstaller bundling rules |
| `CANON_RUST_CARGO_WORKSPACE_CROSS_COMPILATION_CONSTITUTION.md` | Rust build/cross-compile rules |
| `CANON_VITE_BUILD_CONFIGURATION_TYPESCRIPT_REACT_TAURI.md` | Frontend build rules |
| `CANON_PNPM_WORKSPACES_MONOREPO_MANAGEMENT.md` | Monorepo structure |
| `CANON_APPLE_NOTARIZATION_PIPELINE_MACOS_DISTRIBUTION_CONSTITUTION.md` | macOS distribution |
| `CANON_WINDOWS_CODE_SIGNING_AUTHENTICODE_CONSTITUTION.md` | Windows distribution |
| `CANON_GITHUB_ACTIONS_SECRETS_MANAGEMENT_CONSTITUTION.md` | CI/CD secrets |
| `AUTO_UPDATER_ARCHITECTURE_REPORT.md` | Auto-update pipeline |
| `END_TO_END_ENCRYPTION_MESSAGING_MEMORY_REPORT.md` | Memory encryption |
| `AUDIT_LOGGING_TAMPER_EVIDENT_RECORDS_REPORT.md` | Audit trail implementation |
| `CONSENT_ARCHITECTURE_LEDGER_REPORT.md` | Consent enforcement |
| `PILLARS.md` (C-PIL01) | Pillar-to-subsystem mappings |
| `GAIA_CANON_INDEX.md` (C-IDX01) | Master index |

---

*C-RT01 — Last updated 2026-05-10. This document is the authoritative source for runtime architecture decisions. Disputes about how two subsystems should connect must be resolved here first, then propagated to subsystem-specific specs.*
