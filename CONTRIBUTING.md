# Contributing to GAIA-OS

> **Read this before touching anything.**  
> GAIA is not a standard open-source project. It has a canon, a philosophy, and a precise architecture. This document is your orientation.

---

## Who This Is For

Whether you are:
- A developer cloning this repo for the first time
- A returning contributor picking up a new sprint
- An AI agent being asked to generate code for GAIA
- Kyle (R0GV3) returning after time away

...this document tells you what exists, how it's organized, and how to work within it.

---

## The Three-Tier Document System

GAIA-OS has three categories of documentation. Understanding the difference is essential.

### Tier 1 — Canon (`canon/` + `docs/knowledge/CANON_*`)

Canon documents are **authoritative and binding**. They define what GAIA is, how she thinks, what she values, and how her systems must behave. No code may contradict canon.

- Lives in: `canon/` (C00–C75+) and `docs/knowledge/CANON_*` and `docs/knowledge/GAIA_CANON_INDEX.md`
- How to identify: filename starts with `CANON_` or has a Canon ID (e.g., `C-AS01`)
- To change: requires explicit authorship review. See `docs/knowledge/CANON_AUTHORSHIP_REALITY_STANDARDS.md` (C-AS01)
- Start here: [`docs/knowledge/GAIA_CANON_INDEX.md`](./docs/knowledge/GAIA_CANON_INDEX.md)

### Tier 2 — Specs (`specs/` + `docs/knowledge/*_SPEC.md` + `docs/knowledge/*_IMPLEMENTATION*`)

Spec documents are **implementation blueprints**. They translate canon intent into concrete data models, API signatures, UI layouts, and system behavior. Code is written to satisfy specs.

- Key specs: `docs/knowledge/SOUL_MIRROR_ENGINE_IMPLEMENTATION_SPEC.md`, `docs/knowledge/USER_ONBOARDING_ANY_USER_SPEC.md`, `docs/knowledge/RUNTIME_ARCHITECTURE_OVERVIEW.md`
- To change: update the spec first, then update the code. Never the reverse.

### Tier 3 — Knowledge (`docs/knowledge/*_REPORT.md`)

Research reports, background reading, and domain explorations. These inform canon and specs but are not binding. They represent the intellectual substrate GAIA is built on.

- Over 200 reports covering everything from quantum mechanics to attachment theory to Rust compilation
- Not required reading to contribute — use as reference when relevant

---

## Architecture in 500 Words

GAIA-OS is a **Tauri v2 desktop application** with three runtime layers:

### 1. Rust Layer (`src-tauri/`)
The host process. Tauri manages the application window, native OS integration, file system access, and IPC between the frontend and the Python sidecar. All security-sensitive operations (consent gates, file writes, cryptographic operations) are enforced here — at the Rust layer — not in the UI.

### 2. Python Sidecar (`src-python/` + `core/`)
A PyInstaller-bundled Python process that runs alongside the Tauri binary. It handles:
- LLM inference routing (`core/inference_router.py`)
- Soul Mirror inference pipeline
- Affect/mood detection
- MotherThread collective field engine
- All AI logic, memory operations, and pattern recognition

The sidecar communicates with Rust via IPC (stdin/stdout JSON protocol). It exposes a FastAPI server (`core/server.py`) on `localhost:8008` for the React frontend.

### 3. React Frontend (`src/` + `ui/`)
Vite + TypeScript + React. Communicates with the Python sidecar via `localhost:8008` HTTP/SSE, and with the Rust layer via Tauri’s `invoke()` command system. The frontend is a thin display layer — no business logic, no data manipulation, no security decisions.

### Data Layer
All user data is stored locally in SQLite databases in Tauri’s app data directory:
- `user_identity.db` — name, preferences
- `user_prefs.db` — consent flags, settings
- `soul_mirror.db` — Soul Mirror signals, patterns, journal
- `memory_store.db` — long-term and session memory
- `consent_ledger.db` — cryptographic consent records

### The Flow
```
User Action (React UI)
  → Tauri invoke() or HTTP fetch to localhost:8008
  → Rust command OR Python FastAPI endpoint
  → SQLite read/write
  → Response streamed back via SSE or Tauri event
  → React UI updates
```

---

## Local Development Setup

### Prerequisites

| Tool | Version | Why |
|---|---|---|
| Python | 3.11+ | Sidecar + core AI logic |
| Rust | stable (via rustup) | Tauri host process |
| Node.js | 20+ | Frontend tooling |
| pnpm | 8+ | Package manager |
| Ollama | latest | Local LLM inference (free, required) |

### Recommended Local Models (ADR-0011)

| Model | Tier | VRAM | Pull Command |
|---|---|---|---|
| `qwen3.5:27b` | PRIMARY (medium complexity) | 16GB | `ollama pull qwen3.5:27b` |
| `gemma3:12b` | FALLBACK (low complexity / fast) | 8GB | `ollama pull gemma3:12b` |
| `deepseek-r1:distill` | HIGH (reasoning tasks) | 8–16GB | `ollama pull deepseek-r1:distill` |

Set in `.env`:
```env
OLLAMA_MODEL=qwen3.5:27b
OLLAMA_FALLBACK_MODEL=gemma3:12b
# GAIA_ALLOW_CLOUD=1   ← uncomment ONLY to opt-in to cloud augmentation
```

### First-Time Setup

```bash
# 1. Clone
git clone https://github.com/R0GV3TheAlchemist/GAIA-OS.git
cd GAIA-OS

# 2. Python dependencies
pip install -r requirements.txt

# 3. Environment
cp .env.example .env
# Edit .env — set OLLAMA_MODEL; cloud keys are optional (see sovereignty principle below)

# 4. Node dependencies
pnpm install

# 5. Run the Python API server only (no Tauri)
bash start.sh
# API available at http://localhost:8008

# 6. Run full desktop app (Tauri + React + Python sidecar)
npm run tauri dev
```

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific module
pytest tests/test_soul_mirror.py -v

# Sovereignty routing tests (ADR-0011)
pytest tests/test_inference_router.py -v
```

---

## The Canon Protocol

Before writing any code that touches GAIA’s core behavior, ask:

1. **Is there a canon document for this?** Check `docs/knowledge/GAIA_CANON_INDEX.md`
2. **Is there a spec for this?** Check `specs/` and `docs/knowledge/*_SPEC.md`
3. **Does my implementation contradict any canon principle?** Especially C-AS01 (authorship standards), C-PIL01 (pillars), and `docs/knowledge/CANON_CEth01_HUMAN_SOVEREIGNTY_ENERGETIC_COMPACT.md`

If you are about to write code that would:
- Collect user data without consent → **Stop. Read the consent architecture.**
- Override a user’s decision → **Stop. Read the Action Gate spec.**
- Store data remotely by default → **Stop. Everything is local-first.**
- Let GAIA claim certainty she doesn’t have → **Stop. Read epistemic labeling canon (C12, C21).**
- Add a cloud LLM provider as a required dependency → **Stop. Read the sovereignty principle below.**

---

## 🔒 Sovereignty Principle (ADR-0011)

> **Cloud LLM calls are optional augmentation. GAIA must remain fully functional on local models alone.**

This is not a preference — it is a structural requirement enforced in `core/inference_router.py`.

**What this means for contributors:**

- **Never declare a cloud LLM provider as a hard dependency.** If your feature requires a cloud API to function, it is not compatible with GAIA’s architecture.
- **Never add cloud providers to the fallback chain.** The fallback chain in `_local_fallback_backend()` contains only local Ollama models. Cloud is opt-in only, enabled explicitly via `GAIA_ALLOW_CLOUD=1` in `.env`.
- **Every new subsystem must have a documented local fallback.** If you add a new AI capability, document its self-hostable equivalent in `docs/adr/ADR-0011-cloud-as-optional-sovereignty.md`.
- **The sovereignty routing test must pass.** `pytest tests/test_inference_router.py -v` must pass on every PR. It simulates cloud provider unavailability (including 403/503 responses) and asserts local fallback activates.

**Why this principle exists:**

In June 2026, Anthropic restricted API access due to U.S. government export controls. Systems that treated Anthropic as a required dependency lost capability overnight. GAIA’s sovereignty principle is a direct structural response to that event. It is enforced at the infrastructure layer — not just stated in documentation.

**See also:** [`docs/adr/ADR-0011-cloud-as-optional-sovereignty.md`](./docs/adr/ADR-0011-cloud-as-optional-sovereignty.md) · [`docs/security/threat_model.md`](./docs/security/threat_model.md) (THREAT-001)

---

## Code Standards

### Python
- Type hints on all functions
- Docstrings on all public methods
- No business logic in `main.py` (entry point only)
- All DB writes go through the appropriate store module — never raw SQL in feature code
- Async where the function touches I/O

### Rust (Tauri)
- All Tauri commands return `Result<T, String>` — no panics surfaced to frontend
- Consent gate checked before any data write command
- File paths always resolved via Tauri’s `app_data_dir()` — never hardcoded

### TypeScript / React
- No business logic in components — components display, hooks manage state, services call APIs
- All Tauri `invoke()` calls wrapped in a service module under `src/services/`
- Accessibility: every interactive element has `aria-label` or visible label
- No `any` types

### Git
- Branch naming: `feature/short-description`, `fix/short-description`, `docs/short-description`
- Commit messages: `type: short description` (e.g., `feat: add soul mirror pattern decay`, `docs: update canon index`)
- No direct pushes to `main` for feature work — PR required
- Canon document changes require a note in the PR description explaining the authorship rationale

---

## What NOT to Build (Yet)

The `simulation/` directory is reserved for **Phase 2 — the OS layer**. Do not build into it until Phase 1 (the Application) is complete and released across all platforms.

Phase 1 is complete when:
- [ ] Windows, macOS, and Linux builds are passing
- [ ] Soul Mirror Engine is implemented and tested
- [ ] Onboarding flow is implemented end-to-end
- [ ] Auth UI flow is complete (G-9)
- [ ] iOS and Android builds are stable (G-11+)

---

## Questions?

GAIA has an answer for almost everything — it’s in the canon. If you’re stuck, start at:

1. [`docs/knowledge/GAIA_CANON_INDEX.md`](./docs/knowledge/GAIA_CANON_INDEX.md) — master index
2. [`ROADMAP.md`](./ROADMAP.md) — where we’re going
3. [`CHANGELOG.md`](./CHANGELOG.md) — where we’ve been

If the answer isn’t there, the gap is a new canon document waiting to be written.

---

*CONTRIBUTING.md is a living document. Update it when the architecture changes.*  
*Last updated: 2026-06-29 by R0GV3 / GAIA Canon — ADR-0011 sovereignty principle added.*
