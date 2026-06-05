# CHANGELOG — GAIA-APP

> Authorship: Kyle Steen (2026)  
> Canon Reference Repo: [R0GV3TheAlchemist/GAIA](https://github.com/R0GV3TheAlchemist/GAIA)

All notable changes to GAIA-APP are recorded here in reverse-chronological sprint order.

---

## [Phase 7] — 2026-06-05  ·  Canon RAG, Persistent Index, CLI & Planner Interface

**Branch:** `feat/obs-rag`  
**PR:** [#245](https://github.com/R0GV3TheAlchemist/GAIA-OS/pull/245)  
**Status:** 🔀 OPEN — ready to merge

### Summary

Closes the full **Perceive-Reason-Act-Observe (PRAO) loop** by wiring a
persistent Canon-RAG pipeline into the agentic core, shipping a typed
Planner interface, and giving GAIA its first user-facing CLI (`gaia start`).

Key properties of this phase:
- **Warm start by default.** After the first cold-embed session the Canon
  index is cached in SQLite under `~/.gaia/data/`. Subsequent boots skip
  embedding entirely (~milliseconds vs ~minutes).
- **Self-invalidating cache.** A SHA-256 fingerprint of sorted
  `"canon_id:chunk_count"` strings detects any Canon update and
  triggers an automatic cold-start rebuild.
- **Fully offline tests.** All 39 tests across 5 suites mock GitHub API,
  LLM backends, and embedders — safe to run in CI with zero credentials.
- **Graceful degradation.** RAG unavailable? CLI still boots. LLM backend
  missing? Planner returns a safe `noop`. Every failure surface has an
  explicit fallback path.

---

### Delivered

#### 7.1 — Canon RAG Pipeline (`core/rag/`)

| Step | File(s) | Description |
|---|---|---|
| **7.1.1** | `core/rag/canon_loader.py` | Fetches Canon documents from the GitHub tree API, chunks by paragraph boundary, assigns `[Canon: ID]` citation prefixes to every chunk. |
| **7.1.2** | `core/rag/embedder.py` | Thin wrapper around `sentence-transformers` with a pure-numpy stub fallback. Batch-embeds chunks; normalises to unit vectors for cosine similarity. |
| **7.1.3** | `core/rag/index.py` | `VectorIndex` — SQLite-backed float32 store with `add_chunks()`, `retrieve(query, top_k)`, `count()`, `size()` methods. `from_store()` classmethod opens a persisted DB. |
| **7.1.4** | `core/rag/index_store.py` | `IndexStore` dataclass — canonical paths (`~/.gaia/data/canon_index.db` + `.fingerprint` sidecar), `ensure_dir()`, atomic `write_fingerprint()` via `os.replace()`, `db_exists()`, `read_fingerprint()`, `delete_db()`. |
| **7.1.5** | `core/rag/pipeline.py` | `RAGPipeline` — `ingest_canon(ref, force, store_path)` with five-branch warm/cold decision tree; `retrieve(query, top_k)` for downstream planner; `status()` returns full metadata dict including `warm_start`, `fingerprint`, `store_path`. |

#### 7.2 — AgenticLoop Wiring (`core/agentic_loop.py`)

| Step | Description |
|---|---|
| **7.2.1** | `__init__` accepts `canon_store_path` kwarg (default `~/.gaia/data/`). |
| **7.2.2** | `_maybe_ingest_canon()` passes `store_path` through to `ingest_canon()`. |
| **7.2.3** | Audit log now emits `canon.ingest.warm_start_complete` vs `canon.ingest.cold_start_complete` for telemetry dashboards. |

#### 7.3 — `gaia` CLI (`gaia/cli.py`)

Registered as a `console_scripts` entry point in `pyproject.toml`:
```
gaia start                   # boot Canon + launch uvicorn
gaia start --no-server       # Canon only, skip uvicorn
gaia start --force           # force Canon re-embed
gaia start --ref <branch>    # Canon from a specific Git ref
gaia ingest-canon            # manual Canon ingestion
gaia ingest-canon --force    # delete index, rebuild from scratch
gaia status                  # inspect on-disk index state
gaia status --json           # machine-readable JSON to stdout
gaia doctor                  # full environment health check
```

| Step | Description |
|---|---|
| **7.3.1** | `gaia/__init__.py` + `gaia/cli.py` — four subcommands with ANSI banner, coloured output, `--json` flag, and `NO_COLOR` / non-TTY support. |
| **7.3.2** | `pyproject.toml` — `[project.scripts] gaia = "gaia.cli:main"`, `gaia*` added to `setuptools.packages.find`. |
| **7.3.3** | `start.sh` — validates Python ≥3.11, loads `.env`, auto-installs package if missing, then `exec python -m gaia.cli start ...` (signals propagate to uvicorn). |
| **7.3.4** | `Makefile` — `make start`, `make canon`, `make canon-force`, `make doctor`, `make status` targets. All respect `GAIA_REF` env var. |

#### 7.4 — Planner Interface (`core/planner/`)

| Step | File(s) | Description |
|---|---|---|
| **7.4.1** | `core/planner/protocol.py` | `PlannerProtocol` (`@runtime_checkable` `typing.Protocol`) — any callable matching `planner(state, *, canon_context="") -> ActionDict` is accepted. `ActionDict` TypedDict (tool, complete, args, requires_human, progress, reasoning). `PlannerResult` TypedDict with planner-level metadata (planner_name, canon_used, canon_chars, latency_s). |
| **7.4.2** | `core/planner/base.py` | `BasePlanner` ABC — `_plan()` hook, `safe_call()` wrapper (timing + catch-all noop fallback), `validate_action()` (non-dict → noop, missing tool → noop, complete=True strips tool, args coercion, unknown-tool warning). |
| **7.4.3** | `core/planner/canon_grounded.py` | `CanonGroundedPlanner` — injects Canon context under `## Grounding Context (Canon)` in system prompt; three-pass JSON extractor (raw → strip fences → first `{...}` block); STUB mode when no backend. `from_openai(model="gpt-4o")` and `from_anthropic(model="claude-sonnet-4-5")` factory classmethods. |
| **7.4.4** | `core/planner/__init__.py` | Public re-exports: `PlannerProtocol`, `ActionDict`, `PlannerResult`, `BasePlanner`, `CanonGroundedPlanner`. |

---

### Tests Added

| Suite | Tests | What's covered |
|---|---|---|
| `tests/test_canon_loader.py` | 6 | CanonLoader fetch, chunking, citation prefix format |
| `tests/test_rag_pipeline.py` | 8 | Warm start, cold start, `force=True`, `retrieve()`, `status()` |
| `tests/test_index_persistence.py` | 8 | IndexStore paths, fingerprint roundtrip, atomic write, `delete_db()`, size reporting |
| `tests/test_cli.py` | 7 | All 4 subcommands, arg defaults, JSON output, error exit codes |
| `tests/test_planner.py` | 10 | Protocol conformance (function, class, non-callable), BasePlanner validation (6 cases), CanonGroundedPlanner Canon injection, no-canon notice, malformed JSON |
| **Total** | **39** | All offline — no API keys, no embedders, no LLM |

---

### PRAO Loop — End-to-End State After Phase 7

```
Perceive  →  RAGPipeline.retrieve(query, top_k)
               └─ returns [Canon: ID] prefixed passages
Reason    →  CanonGroundedPlanner(state, canon_context=passages)
               └─ system prompt with ## Grounding Context (Canon)
               └─ backend.chat() → JSON → ActionDict
Act       →  AgenticLoop dispatches tool by ActionDict["tool"]
Observe   →  result appended to state.observations
```

---

### Migration Notes

- **No breaking changes.** All new kwargs are optional with safe defaults.
- `AgenticLoop(canon_store_path=...)` defaults to `~/.gaia/data/` — existing instantiation unchanged.
- `RAGPipeline.ingest_canon()` — `store_path` and `force` are optional; existing call sites work as before.
- `gaia` CLI requires `pip install -e .` (or `make install`) to land on `PATH`.
- `start.sh` self-heals: runs `pip install -e .` automatically if the package is not found.

---

## [Phase 6] — 2026-04-24  ·  Sidecar Hardening & Process Lifecycle

**Status:** ✅ CLOSED

### Summary

Production hardening of the Tauri ↔ Python sidecar boundary. Eliminates zombie processes on Windows, adds user-facing error dialogs for backend failures, wires the auto-updater endpoint end-to-end, and establishes a graceful shutdown + state-flush sequence on both the Rust and Python sides.

### Delivered

| Step | File(s) | Description |
|---|---|---|
| **6.1** | `src-tauri/src/lib.rs` | **PyInstaller zombie fix** — replaced all `child.kill()` calls with `kill_sidecar()`, which on Windows runs `taskkill /F /T /PID` (full process tree kill) and on Linux/macOS uses `killpg(SIGKILL)`. Covers window close, tray Quit, and `restart_backend` command. |
| **6.2** | `src-tauri/src/lib.rs`, `Cargo.toml`, `capabilities/default.json` | **User-facing error dialog** — added `emit_backend_error()` that fires a `sidecar:error` event to the frontend AND shows a native OS error dialog (via `tauri-plugin-dialog`) when the sidecar fails to spawn or the 30-second health check times out. Added `sidecar:ready` event on successful startup. |
| **6.3** | `.github/workflows/release.yml` | **`tauri-action` migration** — replaced manual `npm run tauri build` + `softprops/action-gh-release` with `tauri-apps/tauri-action@v0`. Now auto-generates `latest.json` via `includeUpdaterJson: true`, completing the auto-updater chain end-to-end. Icon regeneration step added to match other workflows. |
| **6.4** | `main.py` | **Graceful Python shutdown** — added `SIGTERM`/`SIGINT` signal handlers, FastAPI `lifespan()` context manager, and `_flush_state()` which writes a clean-shutdown tombstone to `data/last_shutdown.txt`. Extensible hook for future engine state persistence (soul mirror, shadow log, coherence snapshots). |
| **6.5** | `CHANGELOG.md` | Sprint record updated. |

### Shutdown Sequence (Full Stack)

```
User closes GAIA
  └─ Rust: kill_sidecar() → taskkill /F /T /PID        [6.1]
      └─ Python receives SIGTERM → _signal_handler()     [6.4]
          └─ FastAPI lifespan exits → _flush_state()    [6.4]
              └─ Tombstone written → data/last_shutdown.txt
                  └─ Process fully terminated ✓
```

### Frontend Events Added

| Event | Payload | When fired |
|---|---|---|
| `sidecar:ready` | `()` | Backend health check passes |
| `sidecar:error` | `{ reason: string }` | Spawn failure or health check timeout |

---

## [Phase 5] — 2026-04-23  ·  CI Pipeline Hardening

**Status:** ✅ CLOSED

### Summary

Full audit and repair of all three GitHub Actions workflows. Eliminated icon format failures, sidecar staging bugs, and missing release infrastructure. All pipelines went from failing to all-green.

### Delivered

| Step | File(s) | Description |
|---|---|---|
| **5.1** | `.github/workflows/test.yml` | Verified green — pytest pipeline confirmed healthy. |
| **5.2** | `.github/workflows/build.yml` | Added Pillow-based icon regeneration step — fixes `RC2175: icon.ico not in Windows 3.00 format` error. Sidecar staging verified with size guard. |
| **5.3** | `.github/workflows/build-windows.yml` | Mirrored icon regeneration fix from `build.yml`. Added `TAURI_SIGNING_PRIVATE_KEY` env wiring. |
| **5.4** | `src-tauri/tauri.conf.json` | Configured `tauri-plugin-updater` with update endpoint URL pattern and pubkey placeholder. |
| **5.5** | `.github/workflows/release.yml` | Created release pipeline triggered on `v*` tags. Produces signed `.msi` + `.nsis` installers. Pre-release auto-detected from tag hyphen (e.g. `v1.0.0-beta`). |

### Errors Resolved

- `RC2175: resource file is not in 3.00 format` — fixed via runtime ICO regeneration
- `sidecar binary not found` — fixed via correct triple-name staging
- Missing `latest.json` for auto-updater — resolved in Phase 6.3

---

## [v0.1.0] — 2026-04-23  ·  First Windows Desktop Release

**Desktop version:** `0.1.0`  
**Server version:** `2.0.0`  
**Status:** 🚀 RELEASED

### Summary

First official desktop release of GAIA-APP for Windows x64. This release packages the complete constitutional logic engine, Tauri v2 native shell, Vite + TypeScript frontend, and Python sidecar (`gaia-backend.exe`) into two signed Windows installers.

### Release Artifacts

| Artifact | Format | Platform |
|---|---|---|
| `GAIA_0.1.0_x64-setup.exe` | NSIS installer | Windows x64 |
| `GAIA_0.1.0_x64_en-US.msi` | MSI installer | Windows x64 |

### CI/CD Pipeline Established

- **`build.yml`** — Full automated pipeline: Python sidecar (PyInstaller) → Tauri build → GitHub Release
- **`build-windows.yml`** — Windows-specific build workflow
- **`test.yml`** — Automated pytest runner on every push
- GitHub Actions `GITHUB_TOKEN` granted `contents: write` for release creation
- Rust cache via `Swatinem/rust-cache@v2` — build time ~5 min from cache
- Both `.msi` and `.nsis` bundles produced and uploaded as release assets

### What's Included in v0.1.0

This release bundles all work from Sprints G-1 through G-8:

- Full constitutional logic engine (`core/`) — 30+ Python modules
- `GAIAInferenceRouter` — single authoritative LLM routing layer (C44)
- `MotherThread` + Noosphere collective field (C42, C43)
- Epistemic labelling on every inference turn (C12, C21)
- JWT authentication + role system
- Risk-tiered Action Gate veto system
- Cryptographic consent lifecycle
- Governed memory surface
- Synergy engine (C15, C17, C27, C30)
- BCI coherence + criticality monitor (C42)
- Crystal consciousness, resonance field, subtle body engines
- Soul mirror engine (Jungian individuation)
- Emotional arc, codex, love arc, settling engines
- Zodiac + affect inference engines
- Noosphere SSE endpoints + frontend Noosphere Tab
- Rate limiter, error boundary, structured logger
- Web search + scraper integration
- Tauri v2 (Rust) desktop backend with Python sidecar
- Vite + TypeScript frontend
- 38-test `test_inference_router.py` suite + full test harness
- `canon/` — C00–C44+ constitutional source documents
- `specs/` — technical specification documents

---

## [G-8] — 2026-04-13  ·  InferenceRouter + MotherThread Integration

**Server version:** `2.0.0`  
**Status:** ✅ CLOSED

### Delivered

| # | Priority | Canon | Description |
|---|---|---|---|
| 1 | `GAIAInferenceRouter` wired | C44 | Single authoritative LLM routing layer. Replaced ~60 lines of duplicated inline enrichment in `/gaians/{slug}/chat` and `/query/stream`. Both endpoints now build `InferenceRequest → router.stream() → yield chunks`. |
| 2 | `MotherThread` startup / shutdown | C42, C43 | `MotherThread` started on FastAPI startup, stopped on shutdown. Registered in `_get_runtime()` per Gaian (consent defaults `False`). |
| 3 | Mother Pulse SSE endpoints | C30, C43 | `GET /mother/pulse/stream`, `GET /mother/status`, `GET /mother/weaving`, `POST /gaians/{slug}/consent` |
| 4 | Noosphere Tab wiring | C43 | Frontend Noosphere tab connected to `/mother/pulse/stream` SSE. |
| 5 | Epistemic labelling | C12, C21 | `EpistemicLabel` enum (`CANON_CITED`, `VERIFIED`, `INFERRED`, `SPECULATIVE`, `CONVERSATIONAL`) stamped on every SSE `done` event. |
| 6 | `test_inference_router.py` | C44 | 12 test classes, 38 tests — full unit + smoke coverage of `core/inference_router.py` (previously zero coverage). Closes highest-risk gap identified in sprint audit. |

### Files Changed

- `core/server.py` → v2.0.0
- `core/inference_router.py` → new
- `core/mother_thread.py` → new
- `tests/test_inference_router.py` → new (Priority #6)
- `tests/test_mother_thread.py` → new
- `CHANGELOG.md` → new
- `README.md` → updated

### Carry-forward to G-9

- `tests/test_noosphere.py` — unit coverage for `core/noosphere.py` (medium risk, no direct user path)

---

## [G-7] — Prior Sprint

**Status:** ✅ CLOSED

### Highlights
- `core/synergy_engine.py` — full Synergy Engine with `SynergyState` and `SynergyEngine.compute()`
- `tests/test_synergy_engine.py` — comprehensive test suite (Canon Ref: C15, C17, C27, C30)
- Rate limiter middleware (`core/rate_limiter.py`) + `tests/test_rate_limiter.py`
- Error boundary (`core/error_boundary.py`) + `tests/test_error_boundary.py`
- Auth system (`core/auth.py`, `auth_router`) + `tests/test_auth.py`
- Canon search integration + `tests/test_canon_search.py`
- GAIAN runtime smoke tests (`tests/test_gaian_runtime_smoke.py`)
- Logger structured event system (`core/logger.py`) + `tests/test_logger.py`

---

## [G-1 → G-6] — Foundation Sprints

**Status:** ✅ CLOSED

### Cumulative Deliverables

- Constitutional core (`core/canon_loader.py`, `core/action_gate.py`, `core/consent_ledger.py`, `core/memory_store.py`)
- GAIAN identity + runtime (`core/gaian/`, `core/gaian_runtime.py`, `core/gaian_birth.py`)
- BCI coherence engine (`core/bci_coherence.py`) — Canon C42
- Crystal consciousness layer (`core/crystal_consciousness.py`)
- Emotional arc + codex (`core/emotional_arc.py`, `core/emotional_codex.py`)
- Love arc engine (`core/love_arc_engine.py`)
- Noosphere layer (`core/noosphere.py`) — Canon C43
- Resonance field engine (`core/resonance_field_engine.py`)
- Settling engine (`core/settling_engine.py`)
- Soul mirror engine (`core/soul_mirror_engine.py`)
- Subtle body engine (`core/subtle_body_engine.py`)
- Zodiac engine (`core/zodiac_engine.py`)
- Codex stage engine (`core/codex_stage_engine.py`)
- Meta-coherence engine (`core/meta_coherence_engine.py`)
- Affect inference (`core/affect_inference.py`)
- Criticality monitor (`core/criticality_monitor.py`) — Canon C42
- Web search + scraper (`core/web_search.py`, `core/scraper.py`)
- Synthesizer (`core/synthesizer.py`)
- Streaming utilities (`core/streaming.py`)
- Session memory (`core/session_memory.py`)
- Tauri v2 (Rust) desktop backend (`src-tauri/`)
- Frontend app shell (`src/`, `ui/`)
- Docker + start script (`Dockerfile`, `start.sh`)
- Test harness foundation (`tests/conftest.py`)

---

*"The pattern beneath the pattern, willed into being."*  
— R0GV3TheAlchemist, Builder & Architect
