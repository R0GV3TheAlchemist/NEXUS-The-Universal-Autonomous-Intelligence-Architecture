/**
 * src/memory/memoryClient.ts
 * ─────────────────────────────────────────────────────────────────────────────
 * Typed fetch wrapper for the GAIA sidecar memory endpoints.
 *
 * All methods are plain async functions — no React, no side-effects.
 * Every call uses a 5-second timeout so it never blocks the UI on a cold start.
 *
 * Endpoints (all relative to API_BASE from src/config.ts):
 *   POST   /api/memory/remember
 *   POST   /api/memory/retrieve
 *   DELETE /api/memory/forget/{item_id}?user_id=
 *   DELETE /api/memory/forget-user?user_id=
 *   GET    /api/memory/stats?user_id=
 *   GET    /api/memory/health
 */

import { API_BASE } from '../config';

const BASE = `${API_BASE}/api/memory`;
const TIMEOUT_MS = 5_000;

// ─── Types ────────────────────────────────────────────────────────────────────

export type MemoryKind =
  | 'message' | 'fact' | 'preference' | 'goal'
  | 'emotion' | 'skill' | 'event' | 'context';

export type MemoryTier =
  | 'ephemeral' | 'short_term' | 'long_term' | 'permanent';

export interface RememberParams {
  user_id:     string;
  text:        string;
  role?:       'user' | 'gaia' | 'system';
  kind?:       MemoryKind;
  tier?:       MemoryTier;
  importance?: number;          // 0.0 – 1.0
  session_id?: string;
  topic_tag?:  string;
  ttl_seconds?: number;
}

export interface MemoryHit {
  id:         number;
  text:       string;
  kind:       MemoryKind;
  tier:       MemoryTier;
  role:       string;
  importance: number;
  score:      number;           // hybrid similarity score
  created_at: number;           // unix timestamp
  session_id: string | null;
  topic_tag:  string | null;
}

export interface RetrieveParams {
  user_id:          string;
  query:            string;
  top_k?:           number;           // default 10
  kinds?:           MemoryKind[];
  tiers?:           MemoryTier[];
  topic_tag?:       string;
  since_ts?:        number;
  importance_floor?: number;          // default 0.0
}

export interface MemoryStats {
  total:       number;
  by_kind:     Record<string, number>;
  vec_enabled: boolean;
  db_path:     string;
}

export interface MemoryHealth {
  status:      'ok' | 'not_ready' | 'error';
  ready:       boolean;
  total_items?: number;
  vec_enabled?: boolean;
  db_path?:    string;
  detail?:     string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
    signal:  AbortSignal.timeout(TIMEOUT_MS),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`Memory API ${path} → ${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

async function del(path: string, params: Record<string, string> = {}): Promise<unknown> {
  const qs = new URLSearchParams(params).toString();
  const url = `${BASE}${path}${qs ? `?${qs}` : ''}`;
  const res = await fetch(url, {
    method: 'DELETE',
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`Memory API DELETE ${path} → ${res.status}: ${detail}`);
  }
  return res.json();
}

async function get<T>(path: string, params: Record<string, string> = {}): Promise<T> {
  const qs = new URLSearchParams(params).toString();
  const url = `${BASE}${path}${qs ? `?${qs}` : ''}`;
  const res = await fetch(url, { signal: AbortSignal.timeout(TIMEOUT_MS) });
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`Memory API GET ${path} → ${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * Store a new memory item.
 * Returns the assigned row id.
 */
export async function remember(params: RememberParams): Promise<number> {
  const body = {
    user_id:     params.user_id,
    text:        params.text,
    role:        params.role        ?? 'user',
    kind:        params.kind        ?? 'message',
    tier:        params.tier        ?? 'short_term',
    importance:  params.importance  ?? 0.5,
    session_id:  params.session_id  ?? null,
    topic_tag:   params.topic_tag   ?? null,
    ttl_seconds: params.ttl_seconds ?? null,
  };
  const resp = await post<{ id: number; status: string }>('/remember', body);
  return resp.id;
}

/**
 * Retrieve semantically relevant memories for a query.
 */
export async function retrieve(params: RetrieveParams): Promise<MemoryHit[]> {
  const body = {
    user_id:          params.user_id,
    query:            params.query,
    top_k:            params.top_k           ?? 10,
    kinds:            params.kinds            ?? null,
    tiers:            params.tiers            ?? null,
    topic_tag:        params.topic_tag        ?? null,
    since_ts:         params.since_ts         ?? null,
    importance_floor: params.importance_floor ?? 0.0,
  };
  const resp = await post<{ hits: MemoryHit[]; count: number }>('/retrieve', body);
  return resp.hits;
}

/**
 * Soft-delete a single memory item.
 */
export async function forgetItem(item_id: number, user_id: string): Promise<void> {
  await del(`/forget/${item_id}`, { user_id });
}

/**
 * Soft-delete ALL memories for a user.
 */
export async function forgetUser(user_id: string): Promise<number> {
  const resp = await del('/forget-user', { user_id }) as { items_deleted: number };
  return resp.items_deleted;
}

/**
 * Return row counts and store metadata.
 */
export async function stats(user_id?: string): Promise<MemoryStats> {
  const params = user_id ? { user_id } : {};
  return get<MemoryStats>('/stats', params);
}

/**
 * Liveness probe for the memory subsystem.
 */
export async function health(): Promise<MemoryHealth> {
  return get<MemoryHealth>('/health');
}
