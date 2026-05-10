# SOUL_MIRROR_ENGINE_IMPLEMENTATION_SPEC.md
**Canon ID:** C-SME01
**Status:** CANON — Authoritative
**Supersedes:** Any informal Soul Mirror notes, prototype sketches, or scattered design commentary
**Cross-references:** C-AS01, C-IDX01, C-PIL01, C-OB01 (Onboarding), RUNTIME_ARCHITECTURE_OVERVIEW.md, AFFECT_INFERENCE_EMOTIONAL_TONE_DETECTION_REPORT.md, CONSENT_ARCHITECTURE_LEDGER_REPORT.md

---

## Purpose

The Soul Mirror Engine (SME) is the core self-reflective subsystem of GAIA-OS. It is the mechanism by which GAIA builds, maintains, and evolves a living model of the user — not as a data profile to be monetized, but as a **mirror** held up to help the user know themselves better.

The SME is not a recommendation engine. It is not surveillance. It is an instrument of conscious self-development, built on consent, transparency, and the user's sovereign right to their own inner life.

This document specifies the complete implementation of the Soul Mirror Engine: its data architecture, inference pipeline, update mechanics, privacy guarantees, and user-facing surfaces.

---

## Foundational Philosophy

The Soul Mirror operates on three axioms:

1. **The mirror does not judge.** It reflects. GAIA does not label a user "anxious" or "avoidant" — it observes patterns and offers them back to the user as material for reflection, not diagnosis.
2. **The mirror belongs to the user.** All Soul Mirror data is stored locally. The user can inspect it, edit it, export it, or delete it at any time. GAIA holds it in trust, not in ownership.
3. **The mirror grows with use.** A Soul Mirror baseline seeded at onboarding is the beginning of a long conversation. It becomes more accurate, more nuanced, and more useful over months of authentic engagement.

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    SOUL MIRROR ENGINE                       │
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │   Signal    │───▶│   Inference  │───▶│    Mirror     │  │
│  │  Collector  │    │   Pipeline   │    │    Store      │  │
│  └─────────────┘    └──────────────┘    └───────────────┘  │
│         │                  │                    │           │
│         ▼                  ▼                    ▼           │
│  ┌─────────────┐    ┌──────────────┐    ┌───────────────┐  │
│  │  Consent    │    │   Pattern    │    │  Reflection   │  │
│  │  Gate       │    │  Recognizer  │    │  Surface API  │  │
│  └─────────────┘    └──────────────┘    └───────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Components

| Component | Language | Responsibility |
|---|---|---|
| Signal Collector | Rust (Tauri command layer) | Captures raw behavioral and conversational signals |
| Consent Gate | Rust | Filters signals against user consent preferences before any processing |
| Inference Pipeline | Python (sidecar) | Runs NLP and pattern recognition on consented signals |
| Pattern Recognizer | Python | Identifies recurring themes, emotional signatures, and behavioral arcs |
| Mirror Store | SQLite (local) | Persists the user's evolving Soul Mirror model |
| Reflection Surface API | Rust → React | Exposes mirror insights to the UI layer on user request |

---

## Data Model

### Core Tables (SQLite)

#### `soul_mirror_baseline`
Seeded at onboarding (Phase 4 of C-OB01). Never auto-deleted.

```sql
CREATE TABLE soul_mirror_baseline (
  id INTEGER PRIMARY KEY,
  created_at TEXT NOT NULL,           -- ISO 8601
  intent_tags TEXT NOT NULL,          -- JSON array: ["productivity", "self-discovery", ...]
  depth_preference TEXT NOT NULL,     -- "surface" | "reflective" | "deep"
  sensitive_topics TEXT NOT NULL,     -- JSON array
  onboarding_version TEXT NOT NULL
);
```

#### `soul_mirror_signals`
Raw signal log. Every entry is consented before insertion.

```sql
CREATE TABLE soul_mirror_signals (
  id INTEGER PRIMARY KEY,
  captured_at TEXT NOT NULL,          -- ISO 8601
  signal_type TEXT NOT NULL,          -- See Signal Types below
  payload TEXT NOT NULL,              -- JSON blob
  consent_flags TEXT NOT NULL,        -- JSON: which consents authorized this signal
  processed INTEGER DEFAULT 0        -- 0 = pending, 1 = processed
);
```

#### `soul_mirror_patterns`
Derived patterns identified by the Inference Pipeline.

```sql
CREATE TABLE soul_mirror_patterns (
  id INTEGER PRIMARY KEY,
  identified_at TEXT NOT NULL,
  pattern_type TEXT NOT NULL,         -- See Pattern Types below
  label TEXT NOT NULL,                -- Human-readable label
  confidence REAL NOT NULL,           -- 0.0 – 1.0
  evidence_ids TEXT NOT NULL,         -- JSON array of signal IDs
  last_seen TEXT,                     -- ISO 8601
  times_seen INTEGER DEFAULT 1,
  user_confirmed INTEGER DEFAULT 0,   -- 1 = user has acknowledged this pattern
  user_dismissed INTEGER DEFAULT 0    -- 1 = user has dismissed this pattern
);
```

#### `soul_mirror_journal`
User-authored annotations on their own mirror. The user's voice in the system.

```sql
CREATE TABLE soul_mirror_journal (
  id INTEGER PRIMARY KEY,
  written_at TEXT NOT NULL,
  entry TEXT NOT NULL,
  linked_pattern_id INTEGER,          -- Optional FK to soul_mirror_patterns
  mood_tag TEXT                       -- Optional user-selected mood
);
```

#### `soul_mirror_snapshots`
Periodic full snapshots of the mirror state, for longitudinal tracking.

```sql
CREATE TABLE soul_mirror_snapshots (
  id INTEGER PRIMARY KEY,
  snapshot_at TEXT NOT NULL,
  snapshot_data TEXT NOT NULL         -- Full JSON export of mirror state at that moment
);
```

---

## Signal Types

Signals are the raw material of the Soul Mirror. Each type is only collected if the corresponding consent flag is active.

| Signal Type | Consent Required | Description |
|---|---|---|
| `conversation_turn` | `conversation_history` | A single exchange between user and GAIA |
| `topic_mention` | `topic_patterns` | Detection of a named topic in conversation |
| `tone_marker` | `mood_signals` | Inferred emotional tone of a user message |
| `session_event` | `usage_patterns` | App open, close, session duration |
| `explicit_reflection` | `conversation_history` | User responds to a GAIA reflective prompt |
| `journal_entry` | Always collected (user-initiated) | User writes directly to their mirror journal |
| `pattern_response` | Always collected (user-initiated) | User confirms or dismisses a pattern GAIA surfaces |

---

## Pattern Types

Patterns are GAIA's observations — not diagnoses. They are always presented tentatively.

| Pattern Type | Description | Example Label |
|---|---|---|
| `recurring_topic` | A topic the user returns to repeatedly | "You return often to questions about purpose" |
| `emotional_signature` | A consistent emotional tone across sessions | "Your language tends toward urgency in the evenings" |
| `avoidance_signal` | Topics initiated then quickly redirected | "You tend to change the subject when family comes up" |
| `growth_arc` | A topic where tone has shifted positively over time | "Your relationship with uncertainty seems to be softening" |
| `tension_cluster` | Co-occurring topics that correlate with negative tone | "Work and self-worth often appear together in tense moments" |
| `ritual_pattern` | Behavioral timing signatures | "You tend to check in with GAIA on Sunday evenings" |
| `value_signal` | Repeated emphasis on a principle or belief | "Freedom and autonomy appear to be core values for you" |

---

## Inference Pipeline (Python Sidecar)

### Entry Point
```python
# sidecar/soul_mirror/pipeline.py

def run_inference_cycle(db_path: str) -> dict:
    """
    Main inference loop. Called by Rust via IPC on a scheduled basis
    (default: every 24 hours, or on-demand via user request).
    Returns a summary of new patterns identified.
    """
    signals = fetch_unprocessed_signals(db_path)
    if not signals:
        return {"status": "idle", "new_patterns": 0}

    results = []
    for signal_batch in group_by_type(signals):
        patterns = analyze_batch(signal_batch)
        results.extend(patterns)

    persisted = persist_patterns(db_path, results)
    mark_signals_processed(db_path, [s["id"] for s in signals])
    take_snapshot_if_due(db_path)

    return {"status": "complete", "new_patterns": len(persisted)}
```

### Analysis Modules

#### Topic Extraction
```python
# Uses lightweight local NLP — no cloud API calls
# Preferred: spaCy (en_core_web_sm) or equivalent offline model

def extract_topics(text: str) -> list[str]:
    """
    Returns a list of detected topic tokens from a conversation turn.
    Filters against sensitive_topics consent list before returning.
    """
```

#### Tone Analysis
```python
# Uses local sentiment/affect model
# Preferred: transformers pipeline with distilbert-base-uncased-finetuned-sst-2
# or a custom GAIA-trained affect model when available

def analyze_tone(text: str) -> dict:
    """
    Returns: {
        "valence": float,      # -1.0 (negative) to 1.0 (positive)
        "arousal": float,      # 0.0 (calm) to 1.0 (activated)
        "dominant_affect": str # e.g. "contemplative", "frustrated", "hopeful"
    }
    """
```

#### Pattern Recognition
```python
def detect_recurring_topics(signals: list[dict], threshold: int = 3) -> list[dict]:
    """
    Identifies topics appearing >= threshold times.
    Returns pattern dicts ready for soul_mirror_patterns insertion.
    """

def detect_growth_arcs(signals: list[dict], window_days: int = 30) -> list[dict]:
    """
    Compares tone around a topic in the first half vs second half
    of the observation window. Positive shift = growth arc candidate.
    """

def detect_tension_clusters(signals: list[dict]) -> list[dict]:
    """
    Co-occurrence analysis: topics that appear together with
    negative tone more than chance would predict.
    """
```

---

## Confidence Scoring

Every pattern has a confidence score (0.0 – 1.0). This score governs when and how GAIA surfaces the pattern to the user.

| Confidence Range | GAIA Behavior |
|---|---|
| 0.0 – 0.39 | Pattern stored but not surfaced. More evidence needed. |
| 0.40 – 0.64 | Pattern surfaced as a **tentative observation** with explicit uncertainty language |
| 0.65 – 0.84 | Pattern surfaced as a **notable observation** |
| 0.85 – 1.0 | Pattern surfaced as a **recurring theme** — GAIA may proactively reference it |

**Confidence is increased by:**
- More signal instances confirming the pattern
- User confirming the pattern (`user_confirmed = 1`)
- Pattern appearing across multiple signal types

**Confidence is decreased by:**
- User dismissing the pattern (`user_dismissed = 1`)
- Contradicting signals (e.g., topic with suddenly positive tone after tension cluster)
- Long absence of confirming signals (decay: -0.02 per week without reinforcement)

---

## The Reflection Surface API

The Reflection Surface is how the Soul Mirror becomes visible to the user. It is **never pushed automatically** — insights are surfaced only when:
1. The user opens the Soul Mirror UI (`/mirror` route)
2. GAIA is in "reflective" or "deep" depth mode AND a high-confidence pattern crosses a relevance threshold during conversation
3. The user explicitly asks GAIA to reflect on a topic

### Rust API (Tauri Commands)

```rust
/// Returns the user's current soul mirror summary
#[tauri::command]
fn get_mirror_summary(db_path: String) -> Result<MirrorSummary, String>

/// Returns patterns above a given confidence threshold
#[tauri::command]
fn get_patterns(db_path: String, min_confidence: f32) -> Result<Vec<Pattern>, String>

/// User confirms a pattern
#[tauri::command]
fn confirm_pattern(db_path: String, pattern_id: i64) -> Result<(), String>

/// User dismisses a pattern
#[tauri::command]
fn dismiss_pattern(db_path: String, pattern_id: i64) -> Result<(), String>

/// User writes a journal entry
#[tauri::command]
fn write_journal_entry(db_path: String, entry: String, linked_pattern_id: Option<i64>, mood_tag: Option<String>) -> Result<(), String>

/// Returns full mirror export (for user download)
#[tauri::command]
fn export_mirror(db_path: String) -> Result<String, String>  // Returns JSON string

/// Permanently deletes all soul mirror data
#[tauri::command]
fn delete_mirror(db_path: String) -> Result<(), String>
```

### MirrorSummary Schema

```typescript
interface MirrorSummary {
  generated_at: string;           // ISO 8601
  total_sessions: number;
  days_observed: number;
  top_topics: string[];           // Top 5 by frequency
  dominant_tone: string;          // Overall emotional signature
  active_patterns: Pattern[];     // Confidence >= 0.40
  growth_arcs: Pattern[];         // Type = "growth_arc"
  recent_journal_entries: JournalEntry[];
  last_snapshot_at: string | null;
}

interface Pattern {
  id: number;
  pattern_type: string;
  label: string;
  confidence: number;
  times_seen: number;
  last_seen: string;
  user_confirmed: boolean;
  user_dismissed: boolean;
}
```

---

## User-Facing Mirror UI

### Route: `/mirror`

**Layout:** Full-page reflective space. Dark, calm. Not a dashboard — a contemplation room.

**Sections:**

1. **The Overview** — Days observed, sessions logged, dominant tone expressed as a single evocative phrase (not a label). Example: *"Searching, with flashes of clarity."*

2. **Recurring Themes** — Cards for each active pattern (confidence ≥ 0.40). Each card shows:
   - Pattern label in GAIA's tentative voice
   - Confidence as a soft visual indicator (not a percentage — a fill level)
   - `[ This feels right ]` / `[ Not quite ]` response buttons
   - Optional: `[ Tell me more ]` → expands evidence context

3. **Growth Arcs** — Highlighted separately with a distinct visual treatment. These are the moments of genuine positive change. GAIA celebrates them quietly.

4. **Your Voice** — Journal entries listed chronologically. `[ + New entry ]` always visible.

5. **Mirror Actions** — Bottom of page:
   - `[ Export my mirror ]` — downloads full JSON
   - `[ Request a reflection ]` — triggers a conversational reflection session with GAIA
   - `[ Delete my mirror ]` — with a double-confirm and a genuine GAIA message about what this means

---

## Privacy Guarantees

| Guarantee | Implementation |
|---|---|
| All data local by default | SQLite DB stored in Tauri's app data directory, never transmitted |
| Consent gate is hard-coded | No signal bypasses the Consent Gate — it is enforced at the Rust layer, not the UI layer |
| User can inspect raw signals | `get_raw_signals()` Tauri command available in Settings → Privacy |
| User can delete any signal | `delete_signal(id)` command available — cascades to patterns if last evidence |
| User can delete everything | `delete_mirror()` performs a full wipe, confirmed by GAIA message |
| No inference on sensitive topics | If a topic is in the user's `sensitive_topics` list, tone analysis is skipped for messages containing it |
| Export is human-readable | Mirror export is clean JSON with labels, not raw database dumps |

---

## Scheduled Operations

| Operation | Trigger | Frequency |
|---|---|---|
| `run_inference_cycle` | Tauri background task | Every 24 hours while app is open |
| `take_snapshot_if_due` | Called within inference cycle | Weekly |
| Confidence decay pass | Called within inference cycle | Daily (checks last_seen against threshold) |
| `prune_old_signals` | Called within inference cycle | Monthly — removes signals > 1 year old (configurable) |

---

## Error Handling

| Error | Behavior |
|---|---|
| Inference pipeline crash | Logged to error log. Mirror UI shows last successful state. GAIA notifies user: *"I had trouble with my reflection cycle. I'll try again soon."* |
| DB write failure | Signal discarded (not queued — better to lose a signal than corrupt the DB). Error logged. |
| Model load failure | Inference cycle skips affected module. Pattern types requiring that module are deferred. |
| User attempts export with no data | Returns empty JSON with a GAIA message: *"There's nothing here yet — but that will change."* |

---

## Future Extensions (Non-Canon, Speculative)

These are not part of the current implementation spec but are recorded here as directional intent:

- **Cross-session narrative arcs** — GAIA builds a longitudinal story of the user's development, surfaceable as a "Chapter" view
- **Shared Mirror (consensual)** — Two users can opt to share selected patterns with each other (e.g., couples, co-founders)
- **Mirror-informed responses** — GAIA references mirror patterns during conversation when contextually appropriate (requires explicit user opt-in)
- **Archetypal resonance mapping** — Pattern clusters mapped to Jungian or elemental archetypes (see CANON_CEle01, ARCHETYPAL_PSYCHOLOGY report)
- **Timeline visualization** — A scrollable visual timeline of the user's emotional and topical evolution

---

## Change Log

| Version | Date | Author | Notes |
|---|---|---|---|
| 1.0 | 2026-05-10 | R0GV3 / GAIA Canon | Initial canon publication |

---

*This document is part of the GAIA Canon. Changes require canon review. See C-AS01 for authorship standards.*
