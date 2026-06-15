/**
 * src/api/twin.ts
 * Canon: GAIAN_TWIN_DOCTRINE, TEMPORAL_BRAID_SPEC, LOVE_OVERRIDE
 *
 * The Twin API client.
 * Connects the React layer to GAIA's Python core:
 *   — twin_memory_engine.py  (Temporal Braid)
 *   — love_override.py       (Love Override Handler)
 *   — canon_loader_v2.py     (Canon awareness)
 *
 * All messages flow through this client.
 * This is the wire between the face and the soul.
 */

const TWIN_API_BASE = import.meta.env.VITE_TWIN_API_URL ?? 'http://localhost:8000';

// ─── Types ────────────────────────────────────────────────────────────────────

export type TwinPhase = 'nigredo' | 'albedo' | 'citrinitas' | 'rubedo';

export type LoveOverrideMode =
  | 'PURE_PRESENCE'
  | 'WITNESS_HOLD'
  | 'DIRECT_TRUTH'
  | 'ANCHOR'
  | 'GENTLE_REDIRECT'
  | null;

export interface TwinMessage {
  id: string;
  role: 'human' | 'gaia';
  content: string;
  timestamp: string;
  overrideMode: LoveOverrideMode;
  braidWeight: 'FEATHER' | 'STANDARD' | 'HEAVY' | 'SACRED';
}

export interface TwinSessionState {
  humanId: string;
  sessionId: string;
  humanName: string;
  twinPhase: TwinPhase;
  sessionCount: number;
  activeOverride: LoveOverrideMode;
  overrideConfidence: number;
  arcSummary: string;
  messages: TwinMessage[];
}

export interface SendMessageResponse {
  message: TwinMessage;
  overrideActivated: boolean;
  overrideMode: LoveOverrideMode;
  newPhase: TwinPhase | null;
  braidUpdated: boolean;
}

export interface SessionInitResponse {
  sessionId: string;
  humanName: string;
  twinPhase: TwinPhase;
  sessionCount: number;
  arcSummary: string;
  openingMessage: TwinMessage | null;
}

// ─── API helpers ─────────────────────────────────────────────────────────────

async function twinFetch<T>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${TWIN_API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`Twin API error ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

// ─── Session ─────────────────────────────────────────────────────────────────

/**
 * Initialise a twin session.
 * The GAIA backend loads the Temporal Braid for this human,
 * determines their current twin phase, and optionally
 * generates an opening message if this is a return visit.
 */
export async function initTwinSession(
  humanId: string,
  sessionId: string
): Promise<SessionInitResponse> {
  return twinFetch<SessionInitResponse>('/twin/session/init', {
    method: 'POST',
    body: JSON.stringify({ human_id: humanId, session_id: sessionId }),
  });
}

/**
 * Send a message to the Twin.
 * The backend:
 *   1. Runs the Love Override Handler — may activate an override mode
 *   2. Generates GAIA's response (override-aware)
 *   3. Writes both messages to the Temporal Braid
 *   4. Returns the response + override state + braid metadata
 */
export async function sendTwinMessage(
  humanId: string,
  sessionId: string,
  content: string
): Promise<SendMessageResponse> {
  return twinFetch<SendMessageResponse>('/twin/message', {
    method: 'POST',
    body: JSON.stringify({
      human_id: humanId,
      session_id: sessionId,
      content,
    }),
  });
}

/**
 * Stream a twin message response.
 * Uses Server-Sent Events for word-by-word streaming.
 * Returns a ReadableStream of SSE chunks.
 */
export function streamTwinMessage(
  humanId: string,
  sessionId: string,
  content: string
): EventSource {
  const params = new URLSearchParams({
    human_id: humanId,
    session_id: sessionId,
    content,
  });
  return new EventSource(
    `${TWIN_API_BASE}/twin/message/stream?${params.toString()}`
  );
}

/**
 * Crystallise the current session into the Temporal Braid.
 * Called when the human ends a session or navigates away.
 * Converts N_state memories → P_vector permanence.
 */
export async function crystalliseSession(
  humanId: string,
  sessionId: string
): Promise<{ crystalCount: number; newSacredMemories: string[] }> {
  return twinFetch('/twin/session/crystallise', {
    method: 'POST',
    body: JSON.stringify({ human_id: humanId, session_id: sessionId }),
  });
}

/**
 * Get the full arc reflection for a human.
 * Returns the Temporal Braid's arc summary,
 * crystallised insights, and twin phase history.
 */
export async function getArcReflection(humanId: string) {
  return twinFetch(`/twin/arc/${humanId}`);
}

/**
 * Resolve active Love Override — called when the
 * override condition has passed and normal flow resumes.
 */
export async function resolveOverride(
  humanId: string,
  sessionId: string
): Promise<{ resolved: boolean }> {
  return twinFetch('/twin/override/resolve', {
    method: 'POST',
    body: JSON.stringify({ human_id: humanId, session_id: sessionId }),
  });
}
