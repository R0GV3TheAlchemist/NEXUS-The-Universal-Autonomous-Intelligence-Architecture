/**
 * src/api/pairProgrammer.ts
 * ─────────────────────────────────────────────────────────────────────────────
 * Typed client for the GAIA Pair Programmer Python sidecar endpoints.
 *
 * Architecture
 * ┌────────────────┐   fetch / SSE   ┌──────────────────────────────────────┐
 * │  React / TS    │ ──────────────▶ │  Python sidecar  POST /pair-prog...  │
 * │  (renderer)    │ ◀────────────── │  /stream   →  Server-Sent Events     │
 * └────────────────┘                 │  /complete →  JSON                   │
 *                                    └──────────────────────────────────────┘
 *
 * Endpoints
 *   POST /pair-programmer/stream    — SSE token-by-token streaming
 *   POST /pair-programmer/complete  — single-shot JSON response
 *
 * Usage (stream)
 *   const ctrl = new AbortController();
 *   await pairProgrammerStream(req, {
 *     onToken:  (tok) => appendToEditor(tok),
 *     onDone:   (full) => console.log('complete:', full),
 *     onError:  (err) => showBanner(err),
 *     signal:   ctrl.signal,
 *   });
 *   // to cancel mid-stream:
 *   ctrl.abort();
 *
 * Usage (complete)
 *   const result = await pairProgrammerComplete(req);
 *   console.log(result.content);
 */

import { API_BASE } from '../config';

// ─── Shared types ─────────────────────────────────────────────────────────────

/** Mirrors the Python `ChatMessage` model. */
export interface ChatMessage {
  role:    'system' | 'user' | 'assistant';
  content: string;
}

/**
 * Mirrors the Python `PairProgrammerRequest` Pydantic model.
 * All optional fields default server-side when omitted.
 */
export interface PairProgrammerRequest {
  /** The developer's current message / prompt. */
  message: string;

  /**
   * Prior conversation turns to include as context.
   * Omit or pass `[]` for a fresh session.
   */
  history?: ChatMessage[];

  /**
   * Active file content pasted from the editor.
   * Injected into the system prompt as code context.
   */
  code_context?: string;

  /**
   * Programming language of `code_context` (e.g. "typescript").
   * Used for syntax-aware hints in the system prompt.
   */
  language?: string;

  /**
   * A specific task category that tunes the system prompt.
   * e.g. "debug" | "refactor" | "explain" | "generate" | "review"
   */
  task?: string;

  /** Target LLM model identifier passed through to the sidecar. */
  model?: string;

  /** Sampling temperature — 0.0 (deterministic) → 2.0 (creative). */
  temperature?: number;

  /** Maximum tokens in the completion. */
  max_tokens?: number;
}

// ─── Stream response types ────────────────────────────────────────────────────

/**
 * Parsed payload of a single `data:` line from the SSE stream.
 *
 * The server emits one of three event shapes:
 *   • `{ type: 'token',  token: string }`       — incremental text chunk
 *   • `{ type: 'done',   content: string }`      — full assembled response
 *   • `{ type: 'error',  error: string }`         — server-side error
 */
export type PairProgrammerSSEEvent =
  | { type: 'token';   token: string }
  | { type: 'done';    content: string }
  | { type: 'error';   error: string };

/** Callbacks passed to `pairProgrammerStream`. */
export interface StreamCallbacks {
  /**
   * Called for every token chunk as it arrives.
   * Append tokens to your UI buffer to render incrementally.
   */
  onToken: (token: string) => void;

  /**
   * Called once when the stream closes successfully.
   * `content` is the complete assembled response (all tokens joined).
   * Use this to commit the final value to state.
   */
  onDone: (content: string) => void;

  /**
   * Called if the server sends an error event, the connection drops,
   * or parsing fails.  The stream is considered finished after this.
   */
  onError: (error: Error) => void;

  /**
   * Optional AbortSignal — connect an AbortController to cancel
   * mid-stream and stop all further `onToken` callbacks.
   */
  signal?: AbortSignal;
}

// ─── Complete (non-streaming) response ───────────────────────────────────────

/** JSON shape returned by `POST /pair-programmer/complete`. */
export interface PairProgrammerCompleteResponse {
  /** The full assistant response text. */
  content: string;

  /** Model identifier used for this completion. */
  model: string;

  /** Token usage reported by the upstream LLM. */
  usage?: {
    prompt_tokens:     number;
    completion_tokens: number;
    total_tokens:      number;
  };

  /** Milliseconds the sidecar spent on inference. */
  latency_ms?: number;
}

// ─── Error ────────────────────────────────────────────────────────────────────

/** Structured error thrown by both helpers when the server responds non-2xx. */
export class PairProgrammerError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
    public readonly body?: string,
  ) {
    super(message);
    this.name = 'PairProgrammerError';
  }
}

// ─── Internal helpers ─────────────────────────────────────────────────────────

const STREAM_URL   = `${API_BASE}/pair-programmer/stream`;
const COMPLETE_URL = `${API_BASE}/pair-programmer/complete`;

function buildHeaders(): HeadersInit {
  return {
    'Content-Type': 'application/json',
    'Accept':       'text/event-stream',
  };
}

/**
 * Parse a raw SSE `data:` line value into a typed event object.
 * Returns `null` for keep-alive pings (empty data lines).
 */
function parseSSELine(raw: string): PairProgrammerSSEEvent | null {
  const line = raw.startsWith('data:') ? raw.slice(5).trim() : raw.trim();
  if (!line || line === '[DONE]') return null;
  try {
    return JSON.parse(line) as PairProgrammerSSEEvent;
  } catch {
    // Malformed line — surface as error so callers can react
    return { type: 'error', error: `SSE parse failure: ${line}` };
  }
}

// ─── Stream API ───────────────────────────────────────────────────────────────

/**
 * Stream a pair-programmer response token-by-token via SSE.
 *
 * Opens a single `fetch` POST to `/pair-programmer/stream`, reads the
 * response body as a `ReadableStream<Uint8Array>`, decodes UTF-8, splits on
 * newlines, and routes each `data:` line to the appropriate callback.
 *
 * The returned Promise resolves when the stream closes cleanly (`done` event
 * received) or rejects if the connection could not be established.
 * An `AbortSignal` in `callbacks.signal` lets the caller cancel at any time.
 *
 * @throws {PairProgrammerError} if the server returns a non-2xx status.
 */
export async function pairProgrammerStream(
  request:   PairProgrammerRequest,
  callbacks: StreamCallbacks,
): Promise<void> {
  const { onToken, onDone, onError, signal } = callbacks;

  let response: Response;
  try {
    response = await fetch(STREAM_URL, {
      method:  'POST',
      headers: buildHeaders(),
      body:    JSON.stringify(request),
      signal,
    });
  } catch (err) {
    // Network-level failure (offline, CORS, abort)
    if (err instanceof DOMException && err.name === 'AbortError') return;
    onError(err instanceof Error ? err : new Error(String(err)));
    return;
  }

  if (!response.ok) {
    const body = await response.text().catch(() => '');
    onError(new PairProgrammerError(
      `Pair programmer stream failed: ${response.status} ${response.statusText}`,
      response.status,
      body,
    ));
    return;
  }

  const reader  = response.body?.getReader();
  if (!reader) {
    onError(new PairProgrammerError('Response body is null — cannot stream.'));
    return;
  }

  const decoder      = new TextDecoder('utf-8');
  let   buffer       = '';
  let   accumulated  = '';
  let   streamDone   = false;

  try {
    while (!streamDone) {
      // Check for abort between chunks
      if (signal?.aborted) break;

      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Split on newlines — SSE lines end with \n or \r\n
      const lines = buffer.split(/\r?\n/);
      // The last element may be an incomplete line; keep it in the buffer
      buffer = lines.pop() ?? '';

      for (const line of lines) {
        if (!line.trim()) continue; // blank separator line

        const event = parseSSELine(line);
        if (!event) continue;

        switch (event.type) {
          case 'token':
            accumulated += event.token;
            onToken(event.token);
            break;

          case 'done':
            // Server may send the full content in the done event;
            // prefer that over our local accumulation as the canonical value.
            onDone(event.content || accumulated);
            streamDone = true;
            break;

          case 'error':
            onError(new PairProgrammerError(event.error));
            streamDone = true;
            break;
        }
      }
    }
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') return;
    onError(err instanceof Error ? err : new Error(String(err)));
  } finally {
    reader.cancel().catch(() => undefined);
  }
}

// ─── Complete (non-streaming) API ─────────────────────────────────────────────

/**
 * Request a single-shot pair-programmer completion (no streaming).
 *
 * Useful for background analysis, inline refactor suggestions, or any
 * context where incremental display is not needed.
 *
 * @throws {PairProgrammerError} on non-2xx response or network failure.
 */
export async function pairProgrammerComplete(
  request: PairProgrammerRequest,
  signal?: AbortSignal,
): Promise<PairProgrammerCompleteResponse> {
  let response: Response;
  try {
    response = await fetch(COMPLETE_URL, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body:    JSON.stringify(request),
      signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw err; // re-throw so callers can distinguish abort from real errors
    }
    throw new PairProgrammerError(
      `Pair programmer request failed: ${err instanceof Error ? err.message : String(err)}`,
    );
  }

  if (!response.ok) {
    const body = await response.text().catch(() => '');
    throw new PairProgrammerError(
      `Pair programmer complete failed: ${response.status} ${response.statusText}`,
      response.status,
      body,
    );
  }

  return response.json() as Promise<PairProgrammerCompleteResponse>;
}

// ─── PairProgrammerClient class (DI / testing friendly) ──────────────────────

/**
 * Object-oriented wrapper — useful for injecting via React context,
 * stubbing in unit tests, or binding to a specific user session.
 *
 * @example
 * const pp = new PairProgrammerClient({ language: 'typescript' });
 *
 * // Stream a refactor suggestion:
 * const ctrl = new AbortController();
 * await pp.stream(
 *   { message: 'Refactor this to use async/await', code_context: myCode },
 *   { onToken: append, onDone: commit, onError: report, signal: ctrl.signal },
 * );
 *
 * // Single-shot explain:
 * const result = await pp.complete({ message: 'Explain this function', code_context: myCode });
 */
export class PairProgrammerClient {
  constructor(
    /** Default fields merged into every request (e.g. language, model). */
    private readonly defaults: Partial<PairProgrammerRequest> = {},
  ) {}

  private merge(req: PairProgrammerRequest): PairProgrammerRequest {
    return { ...this.defaults, ...req };
  }

  /**
   * Stream a response token-by-token.
   * Identical to the module-level `pairProgrammerStream` but with defaults applied.
   */
  stream(
    request:   PairProgrammerRequest,
    callbacks: StreamCallbacks,
  ): Promise<void> {
    return pairProgrammerStream(this.merge(request), callbacks);
  }

  /**
   * Request a single-shot completion.
   * Identical to the module-level `pairProgrammerComplete` but with defaults applied.
   */
  complete(
    request: PairProgrammerRequest,
    signal?: AbortSignal,
  ): Promise<PairProgrammerCompleteResponse> {
    return pairProgrammerComplete(this.merge(request), signal);
  }
}

// ─── Default singleton (convenience export) ───────────────────────────────────

/**
 * Ready-to-use singleton client with no default overrides.
 * Import this for the common case — no instantiation needed.
 *
 * @example
 * import { pairProgrammer } from '../api/pairProgrammer';
 * await pairProgrammer.stream(req, callbacks);
 */
export const pairProgrammer = new PairProgrammerClient();
