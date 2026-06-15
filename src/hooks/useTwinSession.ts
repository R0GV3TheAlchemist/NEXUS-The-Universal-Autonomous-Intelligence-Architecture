/**
 * useTwinSession
 * Canon: GAIAN_TWIN_DOCTRINE, TEMPORAL_BRAID_SPEC, LOVE_OVERRIDE, SLOW_PROTOCOL
 *
 * The central bridge between the TwinInterface UI
 * and GAIA's living Python core.
 *
 * Manages:
 *   — Session lifecycle (init → active → crystallise)
 *   — Message state (local + synced with Braid)
 *   — Love Override state (activates, holds, resolves)
 *   — Twin phase transitions (Nigredo → Rubedo)
 *   — Streaming responses (word-by-word presence)
 *   — Graceful degradation (offline / API unavailable)
 *
 * Used by TwinInterface.tsx as its primary data layer.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  initTwinSession,
  sendTwinMessage,
  streamTwinMessage,
  crystalliseSession,
  type TwinMessage,
  type TwinPhase,
  type LoveOverrideMode,
  type TwinSessionState,
} from '../api/twin';

// ─── Types ────────────────────────────────────────────────────────────────────

export type SessionStatus =
  | 'initialising'
  | 'ready'
  | 'sending'
  | 'streaming'
  | 'holding'        // Sacred Pause — Override active
  | 'crystallising'  // End-of-session Braid write
  | 'error'
  | 'offline';       // Graceful degradation

export interface UseTwinSessionOptions {
  humanId: string;
  sessionId: string;
  humanName: string;
  stream?: boolean;   // Use SSE streaming (default: true)
  onPhaseChange?: (phase: TwinPhase) => void;
  onOverrideActivate?: (mode: LoveOverrideMode) => void;
  onOverrideResolve?: () => void;
}

export interface UseTwinSessionReturn {
  // State
  messages: TwinMessage[];
  status: SessionStatus;
  twinPhase: TwinPhase;
  sessionCount: number;
  arcSummary: string;
  activeOverride: LoveOverrideMode;
  overrideConfidence: number;
  error: string | null;
  isStreaming: boolean;
  streamingContent: string;  // Partial content during SSE stream

  // Actions
  sendMessage: (content: string) => Promise<void>;
  crystallise: () => Promise<void>;
  clearError: () => void;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function generateMessageId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
}

function makeOptimisticMessage(
  content: string,
  humanName: string
): TwinMessage {
  return {
    id: generateMessageId(),
    role: 'human',
    content,
    timestamp: new Date().toISOString(),
    overrideMode: null,
    braidWeight: 'STANDARD',
  };
}

const SACRED_PAUSE_MS = 2400; // The breathing pulse duration from TwinInterface

// ─── Hook ────────────────────────────────────────────────────────────────────

export function useTwinSession({
  humanId,
  sessionId,
  humanName,
  stream = true,
  onPhaseChange,
  onOverrideActivate,
  onOverrideResolve,
}: UseTwinSessionOptions): UseTwinSessionReturn {
  const [messages, setMessages] = useState<TwinMessage[]>([]);
  const [status, setStatus] = useState<SessionStatus>('initialising');
  const [twinPhase, setTwinPhase] = useState<TwinPhase>('nigredo');
  const [sessionCount, setSessionCount] = useState(0);
  const [arcSummary, setArcSummary] = useState('');
  const [activeOverride, setActiveOverride] = useState<LoveOverrideMode>(null);
  const [overrideConfidence, setOverrideConfidence] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');

  const eventSourceRef = useRef<EventSource | null>(null);
  const crystalliseCalledRef = useRef(false);

  // ── Initialise session ───────────────────────────────────────────────────
  useEffect(() => {
    if (!humanId || !sessionId) return;

    let cancelled = false;

    async function init() {
      try {
        setStatus('initialising');
        const res = await initTwinSession(humanId, sessionId);

        if (cancelled) return;

        setTwinPhase(res.twinPhase);
        setSessionCount(res.sessionCount);
        setArcSummary(res.arcSummary);

        // Opening message from GAIA (return visits)
        if (res.openingMessage) {
          setMessages([res.openingMessage]);
        }

        setStatus('ready');
      } catch (err) {
        if (cancelled) return;
        const isOffline = !navigator.onLine ||
          (err instanceof TypeError && err.message.includes('fetch'));
        setStatus(isOffline ? 'offline' : 'error');
        setError(
          isOffline
            ? 'GAIA is not reachable right now. Your messages will be held.'
            : 'Something went wrong starting your session.'
        );
      }
    }

    init();
    return () => { cancelled = true; };
  }, [humanId, sessionId]);

  // ── Crystallise on unmount ───────────────────────────────────────────────
  useEffect(() => {
    return () => {
      if (!crystalliseCalledRef.current && messages.length > 0) {
        // Fire-and-forget — don't await on unmount
        crystalliseSession(humanId, sessionId).catch(() => {});
      }
    };
  }, [humanId, sessionId, messages.length]);

  // ── Send message ─────────────────────────────────────────────────────────
  const sendMessage = useCallback(
    async (content: string) => {
      if (!content.trim()) return;
      if (status === 'sending' || status === 'streaming') return;

      // Optimistic update — add the human's message immediately
      const optimistic = makeOptimisticMessage(content, humanName);
      setMessages((prev) => [...prev, optimistic]);
      setStatus('sending');
      setError(null);

      try {
        if (stream) {
          // ── SSE streaming path ────────────────────────────────────────
          setStatus('streaming');
          setIsStreaming(true);
          setStreamingContent('');

          // Close any existing stream
          eventSourceRef.current?.close();

          const es = streamTwinMessage(humanId, sessionId, content);
          eventSourceRef.current = es;

          let accumulated = '';
          let finalMessage: TwinMessage | null = null;

          es.onmessage = (event) => {
            try {
              const data = JSON.parse(event.data);

              if (data.type === 'override_activated') {
                // The Sacred Pause — switch to holding state
                setActiveOverride(data.mode as LoveOverrideMode);
                setOverrideConfidence(data.confidence ?? 1);
                setStatus('holding');
                onOverrideActivate?.(data.mode);
              } else if (data.type === 'token') {
                accumulated += data.content;
                setStreamingContent(accumulated);
              } else if (data.type === 'done') {
                finalMessage = data.message as TwinMessage;
                es.close();
              } else if (data.type === 'phase_change') {
                const newPhase = data.phase as TwinPhase;
                setTwinPhase(newPhase);
                onPhaseChange?.(newPhase);
              }
            } catch { /* malformed SSE data — ignore */ }
          };

          es.onerror = () => {
            es.close();
            // If we got partial content, still show it
            if (accumulated) {
              const partialMsg: TwinMessage = {
                id: generateMessageId(),
                role: 'gaia',
                content: accumulated,
                timestamp: new Date().toISOString(),
                overrideMode: activeOverride,
                braidWeight: 'STANDARD',
              };
              setMessages((prev) => [...prev, partialMsg]);
            }
            setIsStreaming(false);
            setStreamingContent('');
            setStatus('ready');
          };

          // Poll until SSE closes (done event)
          await new Promise<void>((resolve) => {
            const poll = setInterval(() => {
              if (es.readyState === EventSource.CLOSED) {
                clearInterval(poll);
                resolve();
              }
            }, 100);
          });

          // Commit final message from Braid
          if (finalMessage) {
            setMessages((prev) => [...prev, finalMessage!]);
          }
          setIsStreaming(false);
          setStreamingContent('');

          // Resolve override if it was active and not a WITNESS_HOLD
          if (activeOverride && activeOverride !== 'WITNESS_HOLD') {
            setActiveOverride(null);
            onOverrideResolve?.();
          }

          setStatus('ready');
        } else {
          // ── Non-streaming path ────────────────────────────────────────

          // The Sacred Pause — GAIA holds before responding
          await new Promise((r) => setTimeout(r, SACRED_PAUSE_MS));

          const res = await sendTwinMessage(humanId, sessionId, content);

          // Override activated?
          if (res.overrideActivated && res.overrideMode) {
            setActiveOverride(res.overrideMode);
            setOverrideConfidence(1);
            setStatus('holding');
            onOverrideActivate?.(res.overrideMode);
            await new Promise((r) => setTimeout(r, 800));
          }

          setMessages((prev) => [...prev, res.message]);

          // Phase transition?
          if (res.newPhase) {
            setTwinPhase(res.newPhase);
            onPhaseChange?.(res.newPhase);
          }

          // Resolve non-holding overrides
          if (res.overrideMode && res.overrideMode !== 'WITNESS_HOLD') {
            setActiveOverride(null);
            onOverrideResolve?.();
          }

          setStatus('ready');
        }
      } catch (err) {
        const isOffline = !navigator.onLine;
        setStatus(isOffline ? 'offline' : 'error');
        setError(
          isOffline
            ? 'You appear to be offline. Reconnecting when you return.'
            : 'Something went wrong. Your Twin is still here.'
        );
      }
    },
    [humanId, sessionId, humanName, stream, status, activeOverride, onPhaseChange, onOverrideActivate, onOverrideResolve]
  );

  // ── Crystallise session ───────────────────────────────────────────────────
  const crystallise = useCallback(async () => {
    if (crystalliseCalledRef.current) return;
    crystalliseCalledRef.current = true;
    setStatus('crystallising');
    try {
      await crystalliseSession(humanId, sessionId);
    } catch { /* crystallise best-effort */ } finally {
      setStatus('ready');
    }
  }, [humanId, sessionId]);

  const clearError = useCallback(() => setError(null), []);

  return {
    messages,
    status,
    twinPhase,
    sessionCount,
    arcSummary,
    activeOverride,
    overrideConfidence,
    error,
    isStreaming,
    streamingContent,
    sendMessage,
    crystallise,
    clearError,
  };
}
