//! GAIA-OS — Tauri ↔ Python sidecar bridge for Soul Mirror engines
//!
//! This module exposes the SovereignMemory, AffectEngine, StageEngine,
//! and Onboarding HTTP surfaces as Tauri `invoke`-able commands.  Every
//! command is a thin async proxy: it serialises the frontend payload,
//! POSTs/GETs the sidecar on 127.0.0.1:52000, and returns the JSON
//! response verbatim.
//!
//! No business logic lives here — this is pure transport.
//!
//! # Commands
//!
//! | Command              | Method | Sidecar endpoint            |
//! |----------------------|--------|-----------------------------|
//! | `memory_remember`    | POST   | /memory/remember            |
//! | `memory_recall`      | POST   | /memory/recall              |
//! | `memory_semantic`    | POST   | /memory/semantic            |
//! | `memory_key_status`  | GET    | /memory/key-status          |
//! | `memory_key_rotate`  | POST   | /memory/key-rotate          |
//! | `affect_analyze`     | POST   | /affect/analyze             |
//! | `affect_history`     | GET    | /affect/history/{principal} |
//! | `affect_trend`       | GET    | /affect/trend/{principal}   |
//! | `stage_evaluate`     | POST   | /stage/evaluate             |
//! | `seed_soul_mirror`   | POST   | /onboarding/seed            |

use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::Value;

/// Base URL of the Python sidecar.  Matches the port set in main.py and
/// GAIA_SIDECAR_PORT env var (default 52000).
const SIDECAR_BASE: &str = "http://127.0.0.1:52000";

// ── Managed state ──────────────────────────────────────────────────────────────

/// Shared HTTP client stored in Tauri's managed state.
/// Keeps the connection pool alive across all command calls.
pub struct SidecarClient(pub Client);

impl SidecarClient {
    pub fn new() -> Self {
        let client = Client::builder()
            .timeout(std::time::Duration::from_secs(30))
            .build()
            .expect("failed to build reqwest client");
        SidecarClient(client)
    }
}

// ── Shared error helper ────────────────────────────────────────────────────────

async fn sidecar_err(resp: reqwest::Response) -> String {
    let status = resp.status();
    let body = resp.text().await.unwrap_or_default();
    format!("sidecar returned {status}: {body}")
}

// ── /memory commands ───────────────────────────────────────────────────────────

/// Request body for `POST /memory/remember`
#[derive(Serialize)]
struct RememberRequest<'a> {
    principal_id: &'a str,
    content:      &'a str,
    role:         &'a str,  // "user" | "assistant" | "system"
}

/// Request body for `POST /memory/recall`
#[derive(Serialize)]
struct RecallRequest<'a> {
    principal_id: &'a str,
    query:        &'a str,
    limit:        u32,
}

/// Request body for `POST /memory/semantic`
#[derive(Serialize)]
struct SemanticRequest<'a> {
    principal_id: &'a str,
    pattern:      &'a str,
    evidence:     Vec<&'a str>,
}

/// Store a single chat turn in episodic memory.
///
/// Called after every message exchange in the GAIA chat loop.
#[tauri::command]
pub async fn memory_remember(
    state: tauri::State<'_, SidecarClient>,
    principal_id: String,
    content:      String,
    role:         String,
) -> Result<Value, String> {
    let body = RememberRequest {
        principal_id: &principal_id,
        content:      &content,
        role:         &role,
    };
    let resp = state
        .0
        .post(format!("{SIDECAR_BASE}/memory/remember"))
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("memory_remember request failed: {e}"))?;

    if resp.status().is_success() {
        resp.json::<Value>().await.map_err(|e| e.to_string())
    } else {
        Err(sidecar_err(resp).await)
    }
}

/// Retrieve relevant memories to inject into GAIA's context window.
///
/// Called before building the prompt for each inference turn.
#[tauri::command]
pub async fn memory_recall(
    state:        tauri::State<'_, SidecarClient>,
    principal_id: String,
    query:        String,
    limit:        Option<u32>,
) -> Result<Value, String> {
    let body = RecallRequest {
        principal_id: &principal_id,
        query:        &query,
        limit:        limit.unwrap_or(5),
    };
    let resp = state
        .0
        .post(format!("{SIDECAR_BASE}/memory/recall"))
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("memory_recall request failed: {e}"))?;

    if resp.status().is_success() {
        resp.json::<Value>().await.map_err(|e| e.to_string())
    } else {
        Err(sidecar_err(resp).await)
    }
}

/// Distil a semantic pattern from episodic evidence.
#[tauri::command]
pub async fn memory_semantic(
    state:        tauri::State<'_, SidecarClient>,
    principal_id: String,
    pattern:      String,
    evidence:     Vec<String>,
) -> Result<Value, String> {
    let evidence_refs: Vec<&str> = evidence.iter().map(String::as_str).collect();
    let body = SemanticRequest {
        principal_id: &principal_id,
        pattern:      &pattern,
        evidence:     evidence_refs,
    };
    let resp = state
        .0
        .post(format!("{SIDECAR_BASE}/memory/semantic"))
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("memory_semantic request failed: {e}"))?;

    if resp.status().is_success() {
        resp.json::<Value>().await.map_err(|e| e.to_string())
    } else {
        Err(sidecar_err(resp).await)
    }
}

/// Return the current DEK ring + master key health status.
#[tauri::command]
pub async fn memory_key_status(
    state: tauri::State<'_, SidecarClient>,
) -> Result<Value, String> {
    let resp = state
        .0
        .get(format!("{SIDECAR_BASE}/memory/key-status"))
        .send()
        .await
        .map_err(|e| format!("memory_key_status request failed: {e}"))?;

    if resp.status().is_success() {
        resp.json::<Value>().await.map_err(|e| e.to_string())
    } else {
        Err(sidecar_err(resp).await)
    }
}

/// Trigger a forward DEK rotation.
#[tauri::command]
pub async fn memory_key_rotate(
    state: tauri::State<'_, SidecarClient>,
) -> Result<Value, String> {
    let resp = state
        .0
        .post(format!("{SIDECAR_BASE}/memory/key-rotate"))
        .send()
        .await
        .map_err(|e| format!("memory_key_rotate request failed: {e}"))?;

    if resp.status().is_success() {
        resp.json::<Value>().await.map_err(|e| e.to_string())
    } else {
        Err(sidecar_err(resp).await)
    }
}

// ── /affect commands ───────────────────────────────────────────────────────────

/// Request body for `POST /affect/analyze`
#[derive(Serialize)]
struct AffectAnalyzeRequest<'a> {
    principal_id: &'a str,
    text:         &'a str,
    source:       &'a str,  // "gaia_chat" | "journal" | "system"
    persist:      bool,
}

/// Run affect inference on a text block and optionally persist the snapshot.
#[tauri::command]
pub async fn affect_analyze(
    state:        tauri::State<'_, SidecarClient>,
    principal_id: String,
    text:         String,
    source:       Option<String>,
    persist:      Option<bool>,
) -> Result<Value, String> {
    let body = AffectAnalyzeRequest {
        principal_id: &principal_id,
        text:         &text,
        source:       source.as_deref().unwrap_or("gaia_chat"),
        persist:      persist.unwrap_or(true),
    };
    let resp = state
        .0
        .post(format!("{SIDECAR_BASE}/affect/analyze"))
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("affect_analyze request failed: {e}"))?;

    if resp.status().is_success() {
        resp.json::<Value>().await.map_err(|e| e.to_string())
    } else {
        Err(sidecar_err(resp).await)
    }
}

/// Retrieve AffectSnapshot history for a principal (last N days).
#[tauri::command]
pub async fn affect_history(
    state:        tauri::State<'_, SidecarClient>,
    principal_id: String,
    days:         Option<u32>,
) -> Result<Value, String> {
    let days = days.unwrap_or(30);
    let resp = state
        .0
        .get(format!("{SIDECAR_BASE}/affect/history/{principal_id}"))
        .query(&[("days", days)])
        .send()
        .await
        .map_err(|e| format!("affect_history request failed: {e}"))?;

    if resp.status().is_success() {
        resp.json::<Value>().await.map_err(|e| e.to_string())
    } else {
        Err(sidecar_err(resp).await)
    }
}

/// Return the ArcTrend (valence momentum, volatility, direction) for a principal.
#[tauri::command]
pub async fn affect_trend(
    state:        tauri::State<'_, SidecarClient>,
    principal_id: String,
    days:         Option<u32>,
) -> Result<Value, String> {
    let days = days.unwrap_or(30);
    let resp = state
        .0
        .get(format!("{SIDECAR_BASE}/affect/trend/{principal_id}"))
        .query(&[("days", days)])
        .send()
        .await
        .map_err(|e| format!("affect_trend request failed: {e}"))?;

    if resp.status().is_success() {
        resp.json::<Value>().await.map_err(|e| e.to_string())
    } else {
        Err(sidecar_err(resp).await)
    }
}

// ── /stage commands ────────────────────────────────────────────────────────────

/// Run a full Magnum Opus stage evaluation tick for a principal.
///
/// All signal fields are optional — pass only what is available.
/// The sidecar fills defaults for missing fields.
#[tauri::command]
pub async fn stage_evaluate(
    state:                   tauri::State<'_, SidecarClient>,
    principal_id:            String,
    goal_states:             Option<Vec<String>>,
    hrv_rmssd_history:       Option<Vec<f64>>,
    alignment_score_history: Option<Vec<f64>>,
    journal_entries:         Option<Vec<Value>>,
    focus_session_minutes:   Option<Vec<f64>>,
    goals_completed:         Option<u32>,
    goals_abandoned:         Option<u32>,
    valence_history:         Option<Vec<f64>>,
    schumann_state:          Option<Value>,
) -> Result<Value, String> {
    // Build a serde_json::Value payload — all optional fields
    let mut body = serde_json::json!({
        "principal_id": principal_id,
        "goal_states":              goal_states.unwrap_or_default(),
        "hrv_rmssd_history":        hrv_rmssd_history.unwrap_or_default(),
        "alignment_score_history":  alignment_score_history.unwrap_or_default(),
        "journal_entries":          journal_entries.unwrap_or_default(),
        "focus_session_minutes":    focus_session_minutes.unwrap_or_default(),
        "goals_completed":          goals_completed.unwrap_or(0),
        "goals_abandoned":          goals_abandoned.unwrap_or(0),
        "valence_history":          valence_history.unwrap_or_default(),
    });

    if let Some(ss) = schumann_state {
        body["schumann_state"] = ss;
    }

    let resp = state
        .0
        .post(format!("{SIDECAR_BASE}/stage/evaluate"))
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("stage_evaluate request failed: {e}"))?;

    if resp.status().is_success() {
        resp.json::<Value>().await.map_err(|e| e.to_string())
    } else {
        Err(sidecar_err(resp).await)
    }
}

// ── /onboarding commands ───────────────────────────────────────────────────────
//
// Called exactly once per user: when Phase 8 "Enter" is pressed and
// `completeOnboarding()` fires in the TS store.  The payload carries the
// full identity profile collected during onboarding so the Python backend
// can initialise the Soul Mirror, set default memory preferences, and
// pre-populate the user's semantic graph before the first conversation.
//
// The command is fire-and-confirm: it returns Ok(Value) on a 200 response
// from the sidecar, or Err(String) on any transport or HTTP error.  The TS
// caller swallows errors in a catch{} — a failed seed does NOT block the
// user from entering the shell.  The sidecar must be idempotent (re-seeding
// with the same `name` + `completed_at` is a no-op).

/// Consent flags mirroring the TS `ConsentPreferences` interface.
/// All fields are required — the TS store always serialises all six keys.
#[derive(Deserialize)]
pub struct ConsentFlags {
    pub conversation_history: bool,
    pub mood_signals:         bool,
    pub topic_patterns:       bool,
    pub usage_patterns:       bool,
    pub telemetry:            bool,
    pub cloud_backup:         bool,
}

/// Full onboarding payload — mirrors the object built in `seedSoulMirror()`
/// inside `onboardingStore.ts`.
///
/// All string/vec fields use `Option` so that partially-complete onboarding
/// states (e.g. a resume that was interrupted mid-Phase 4) are still accepted
/// gracefully.  `consent` is required because its defaults are baked in at
/// Phase 5 and cannot be absent by Phase 8.
#[derive(Deserialize)]
pub struct OnboardingResponses {
    /// User's chosen name (Phase 3)
    pub name:             Option<String>,
    /// Primary intents, e.g. ["productivity", "building"] (Phase 4)
    pub intent:           Option<Vec<String>>,
    /// Free-text elaboration when intent includes "other" (Phase 4)
    pub intent_other:     Option<String>,
    /// Memory depth tier: "surface" | "reflective" | "deep" (Phase 4)
    pub depth_preference: Option<String>,
    /// Topics to handle with extra care (Phase 4)
    pub sensitive_topics: Option<Vec<String>>,
    /// Six-flag consent record (Phase 5)
    pub consent:          ConsentFlags,
    /// ISO-8601 timestamp from `completeOnboarding()` (Phase 8)
    pub completed_at:     Option<String>,
}

/// Seed the Soul Mirror with the user's onboarding responses.
///
/// Forwards the payload verbatim to `POST /onboarding/seed` on the Python
/// sidecar.  Returns the sidecar's JSON response (a summary of what was
/// initialised) or an error string.
///
/// # Sidecar contract
/// The Python endpoint is expected to:
///   1. Create / update the user's principal profile
///   2. Write depth-preference into the SovereignMemory config
///   3. Write consent flags into the privacy policy store
///   4. Pre-populate the semantic graph with intent-derived seeds
///   5. Return `{ "status": "seeded", "principal_id": "..." }`
///
/// The endpoint MUST be idempotent — calling it twice with the same
/// `completed_at` timestamp must be a no-op.
#[tauri::command]
pub async fn seed_soul_mirror(
    state:     tauri::State<'_, SidecarClient>,
    responses: OnboardingResponses,
) -> Result<Value, String> {
    // Build the JSON body to forward. We use serde_json::json! rather than
    // directly serialising OnboardingResponses so we can emit all fields
    // explicitly and keep the sidecar contract visible in one place.
    let body = serde_json::json!({
        "name":             responses.name.as_deref().unwrap_or(""),
        "intent":           responses.intent.unwrap_or_default(),
        "intent_other":     responses.intent_other.as_deref().unwrap_or(""),
        "depth_preference": responses.depth_preference.as_deref().unwrap_or("reflective"),
        "sensitive_topics": responses.sensitive_topics.unwrap_or_default(),
        "completed_at":     responses.completed_at.as_deref().unwrap_or(""),
        "consent": {
            "conversation_history": responses.consent.conversation_history,
            "mood_signals":         responses.consent.mood_signals,
            "topic_patterns":       responses.consent.topic_patterns,
            "usage_patterns":       responses.consent.usage_patterns,
            "telemetry":            responses.consent.telemetry,
            "cloud_backup":         responses.consent.cloud_backup,
        },
    });

    let resp = state
        .0
        .post(format!("{SIDECAR_BASE}/onboarding/seed"))
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("seed_soul_mirror request failed: {e}"))?;

    if resp.status().is_success() {
        resp.json::<Value>().await.map_err(|e| e.to_string())
    } else {
        Err(sidecar_err(resp).await)
    }
}
