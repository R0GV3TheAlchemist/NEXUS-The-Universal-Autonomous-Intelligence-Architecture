/**
 * src/hooks/useMemory.ts
 * ─────────────────────────────────────────────────────────────────────────────
 * React hook for GAIA's persistent semantic memory layer.
 *
 * Wraps the memoryClient and exposes a clean interface for React components:
 *
 *   const memory = useMemory({ userId: 'user_001', sessionId: 'sess_abc' });
 *
 *   // After receiving the user's message:
 *   await memory.rememberTurn('user', 'I prefer dark mode');
 *
 *   // Before generating a response:
 *   const context = await memory.retrieveContext('dark mode preferences');
 *   const systemPrompt = injectMemoryContext(basePrompt, context);
 *
 *   // Read state:
 *   memory.hits        // MemoryHit[] — last retrieval results
 *   memory.busy        // boolean — request in flight
 *   memory.error       // string | null — last error message
 *
 * ─────────────────────────────────────────────────────────────────────────────
 * Design notes:
 *  - Uses useSyncExternalStore for React 18 concurrent-safe reads.
 *  - A lightweight module-level store keeps state outside the component tree
 *    so multiple components always see the same hits/busy/error.
 *  - All API calls are fire-and-forget or explicitly awaited — never blocking.
 *  - Fails silently in production (logs a warning) so a cold sidecar never
 *    breaks the chat UI.
 */

import { useSyncExternalStore, useCallback } from 'react';
import {
  remember   as apiRemember,
  retrieve   as apiRetrieve,
  forgetItem as apiForgetItem,
  forgetUser as apiForgetUser,
  stats      as apiStats,
  health     as apiHealth,
  MemoryHit,
  MemoryKind,
  MemoryTier,
  MemoryStats,
  MemoryHealth,
  RememberParams,
  RetrieveParams,
} from '../memory/memoryClient';
import { injectMemoryContext } from '../memory/promptMemory';

// ─── Module-level store (shared across all hook instances) ────────────────────

interface MemoryState {
  hits:   MemoryHit[];
  busy:   boolean;
  error:  string | null;
}

type Listener = () => void;

const _listeners = new Set<Listener>();
let _state: MemoryState = { hits: [], busy: false, error: null };

function _setState(patch: Partial<MemoryState>): void {
  _state = { ..._state, ...patch };
  _listeners.forEach(fn => fn());
}

const _store = {
  subscribe: (fn: Listener) => {
    _listeners.add(fn);
    return () => _listeners.delete(fn);
  },
  getSnapshot: () => _state,
};

// ─── Hook options ─────────────────────────────────────────────────────────────

export interface UseMemoryOptions {
  /** The user identifier used for all API calls. */
  userId:     string;
  /** Optional session id attached to remembered items. */
  sessionId?: string;
  /** Default tier for auto-remembered turns (default: 'short_term'). */
  defaultTier?: MemoryTier;
}

// ─── Hook return type ─────────────────────────────────────────────────────────

export interface UseMemoryReturn {
  // ── State ────────────────────────────────────────────────────────────────
  hits:   MemoryHit[];   // last retrieve() results
  busy:   boolean;       // any request in flight
  error:  string | null; // last error message, cleared on next successful call

  // ── Write ────────────────────────────────────────────────────────────────
  /** Store a single text chunk with full control over metadata. */
  remember: (params: Omit<RememberParams, 'user_id'>) => Promise<number | null>;

  /**
   * Convenience: store one turn of conversation.
   * role = 'user' | 'gaia'
   * Automatically scores importance based on role.
   */
  rememberTurn: (
    role: 'user' | 'gaia',
    text: string,
    overrides?: Partial<Omit<RememberParams, 'user_id' | 'role' | 'text'>>
  ) => Promise<number | null>;

  /** Soft-delete a single item by id. */
  forgetItem: (itemId: number) => Promise<void>;

  /** Soft-delete ALL memories for the current user. */
  forgetUser: () => Promise<number>;

  // ── Read ─────────────────────────────────────────────────────────────────
  /**
   * Semantic search — updates `hits` and returns the results.
   * Pass `query` = current user message / topic for best results.
   */
  retrieveContext: (query: string, options?: Partial<RetrieveParams>) => Promise<MemoryHit[]>;

  /**
   * Build the {{memory_context}} string ready to inject into a system prompt.
   * Uses the current `hits` unless you pass a custom set.
   */
  buildMemoryContext: (customHits?: MemoryHit[]) => string;

  /** Full inject helper — wraps injectMemoryContext from promptMemory.ts. */
  injectIntoPrompt: (systemPrompt: string, customHits?: MemoryHit[]) => string;

  // ── Meta ─────────────────────────────────────────────────────────────────
  fetchStats:  (userId?: string) => Promise<MemoryStats | null>;
  fetchHealth: () => Promise<MemoryHealth | null>;
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useMemory(options: UseMemoryOptions): UseMemoryReturn {
  const { userId, sessionId, defaultTier = 'short_term' } = options;

  const state = useSyncExternalStore(
    _store.subscribe,
    _store.getSnapshot,
    _store.getSnapshot,
  );

  // ── remember ──────────────────────────────────────────────────────────────
  const remember = useCallback(async (
    params: Omit<RememberParams, 'user_id'>
  ): Promise<number | null> => {
    _setState({ busy: true, error: null });
    try {
      const id = await apiRemember({ ...params, user_id: userId, session_id: params.session_id ?? sessionId });
      _setState({ busy: false });
      return id;
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      console.warn('[useMemory] remember failed:', msg);
      _setState({ busy: false, error: msg });
      return null;
    }
  }, [userId, sessionId]);

  // ── rememberTurn ──────────────────────────────────────────────────────────
  const rememberTurn = useCallback(async (
    role: 'user' | 'gaia',
    text: string,
    overrides?: Partial<Omit<RememberParams, 'user_id' | 'role' | 'text'>>
  ): Promise<number | null> => {
    if (!text.trim()) return null;
    return remember({
      text,
      role,
      kind:       overrides?.kind       ?? 'message',
      tier:       overrides?.tier       ?? defaultTier,
      importance: overrides?.importance ?? (role === 'gaia' ? 0.6 : 0.5),
      session_id: overrides?.session_id ?? sessionId,
      topic_tag:  overrides?.topic_tag,
      ttl_seconds: overrides?.ttl_seconds,
    });
  }, [remember, sessionId, defaultTier]);

  // ── retrieveContext ───────────────────────────────────────────────────────
  const retrieveContext = useCallback(async (
    query: string,
    options?: Partial<RetrieveParams>
  ): Promise<MemoryHit[]> => {
    _setState({ busy: true, error: null });
    try {
      const hits = await apiRetrieve({
        user_id: userId,
        query,
        top_k:            options?.top_k            ?? 12,
        kinds:            options?.kinds,
        tiers:            options?.tiers,
        topic_tag:        options?.topic_tag,
        since_ts:         options?.since_ts,
        importance_floor: options?.importance_floor ?? 0.1,
      });
      _setState({ hits, busy: false });
      return hits;
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      console.warn('[useMemory] retrieveContext failed:', msg);
      _setState({ busy: false, error: msg });
      return [];
    }
  }, [userId]);

  // ── forgetItem ────────────────────────────────────────────────────────────
  const forgetItem = useCallback(async (itemId: number): Promise<void> => {
    _setState({ busy: true, error: null });
    try {
      await apiForgetItem(itemId, userId);
      // Remove from local hits too
      _setState({ busy: false, hits: _state.hits.filter(h => h.id !== itemId) });
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      console.warn('[useMemory] forgetItem failed:', msg);
      _setState({ busy: false, error: msg });
    }
  }, [userId]);

  // ── forgetUser ────────────────────────────────────────────────────────────
  const forgetUser = useCallback(async (): Promise<number> => {
    _setState({ busy: true, error: null });
    try {
      const count = await apiForgetUser(userId);
      _setState({ busy: false, hits: [] });
      return count;
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      console.warn('[useMemory] forgetUser failed:', msg);
      _setState({ busy: false, error: msg });
      return 0;
    }
  }, [userId]);

  // ── buildMemoryContext ────────────────────────────────────────────────────
  const buildMemoryContext = useCallback((
    customHits?: MemoryHit[]
  ): string => {
    const source = customHits ?? _state.hits;
    if (!source.length) return '';
    return source
      .map((h, i) => `[${i + 1}] (${h.kind}, importance=${h.importance.toFixed(2)}) ${h.text}`)
      .join('\n');
  }, []);

  // ── injectIntoPrompt ──────────────────────────────────────────────────────
  const injectIntoPrompt = useCallback((
    systemPrompt: string,
    customHits?: MemoryHit[]
  ): string => {
    return injectMemoryContext(systemPrompt, customHits ?? _state.hits);
  }, []);

  // ── fetchStats ────────────────────────────────────────────────────────────
  const fetchStats = useCallback(async (
    targetUserId?: string
  ): Promise<MemoryStats | null> => {
    try {
      return await apiStats(targetUserId ?? userId);
    } catch (err) {
      console.warn('[useMemory] fetchStats failed:', err);
      return null;
    }
  }, [userId]);

  // ── fetchHealth ───────────────────────────────────────────────────────────
  const fetchHealth = useCallback(async (): Promise<MemoryHealth | null> => {
    try {
      return await apiHealth();
    } catch (err) {
      console.warn('[useMemory] fetchHealth failed:', err);
      return null;
    }
  }, []);

  // ─────────────────────────────────────────────────────────────────────────
  return {
    hits:              state.hits,
    busy:              state.busy,
    error:             state.error,
    remember,
    rememberTurn,
    forgetItem,
    forgetUser,
    retrieveContext,
    buildMemoryContext,
    injectIntoPrompt,
    fetchStats,
    fetchHealth,
  };
}
