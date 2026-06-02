// GAIA Dev Suite — AI Pair Programmer (Right Sidebar)
// Phase 4.6 — Full implementation

import './RightSidebar.css';
import {
  getSelectedCode,
  getEditorContent,
  getCurrentFilePath,
  insertAtCursor,
  registerGaiaInlineCompletions,
} from './MonacoEditor';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const GAIA_STREAM_ENDPOINT = '/api/pair-programmer/stream';
const GAIA_COMPLETE_ENDPOINT = '/api/pair-programmer/complete';

type PairAction = 'explain' | 'refactor' | 'tests' | 'fix';

interface ActionConfig {
  label: string;
  icon: string;
  description: string;
  requiresSelection: boolean;
}

const ACTIONS: Record<PairAction, ActionConfig> = {
  explain:  { label: 'Explain',  icon: '🔍', description: 'Explain selected code in plain language', requiresSelection: true  },
  refactor: { label: 'Refactor', icon: '✨', description: 'Rewrite selected code more cleanly',       requiresSelection: true  },
  tests:    { label: 'Tests',    icon: '🧪', description: 'Generate unit tests for selected function',  requiresSelection: true  },
  fix:      { label: 'Fix Bug',  icon: '🔧', description: 'Suggest a fix for selected error/code',     requiresSelection: false },
};

// ---------------------------------------------------------------------------
// Module state
// ---------------------------------------------------------------------------

let _activeAction: PairAction = 'explain';
let _streaming = false;
let _lastResponse = '';
let _lastCode = '';
let _abortController: AbortController | null = null;

// ---------------------------------------------------------------------------
// Mount
// ---------------------------------------------------------------------------

export function mountRightSidebar(root: HTMLElement): void {
  root.innerHTML = `
    <div class="right-sidebar" id="rs-root">
      <div class="rs-header">
        <span class="rs-title">⚡ GAIA Pair Programmer</span>
        <button class="rs-stop-btn" id="rs-stop" title="Stop generation" style="display:none;">◼</button>
      </div>

      <div class="rs-tabs" id="rs-tabs" role="tablist">
        ${(Object.entries(ACTIONS) as [PairAction, ActionConfig][]).map(([key, cfg]) => `
          <button
            class="rs-tab ${key === _activeAction ? 'active' : ''}"
            data-action="${key}"
            role="tab"
            aria-selected="${key === _activeAction}"
            title="${cfg.description}"
          >${cfg.icon} ${cfg.label}</button>
        `).join('')}
      </div>

      <div class="rs-context" id="rs-context">
        <span class="rs-context-label" id="rs-context-label">No selection — using full file</span>
      </div>

      <div class="rs-run-bar">
        <button class="rs-run-btn" id="rs-run">▶ Run</button>
        <span class="rs-hint" id="rs-hint">${ACTIONS[_activeAction].description}</span>
      </div>

      <div class="rs-response" id="rs-response">
        <div class="rs-placeholder" id="rs-placeholder">
          Select code in the editor, then press <kbd>Run</kbd>.
        </div>
      </div>
    </div>
  `;

  bindEvents(root);
  registerGaiaInlineCompletions(GAIA_COMPLETE_ENDPOINT);
  startSelectionWatcher();
}

// ---------------------------------------------------------------------------
// Event binding
// ---------------------------------------------------------------------------

function bindEvents(root: HTMLElement): void {
  root.querySelectorAll<HTMLButtonElement>('.rs-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      const action = btn.dataset.action as PairAction;
      setActiveAction(action);
    });
  });

  root.querySelector<HTMLButtonElement>('#rs-run')?.addEventListener('click', runAction);
  root.querySelector<HTMLButtonElement>('#rs-stop')?.addEventListener('click', stopStreaming);
}

function setActiveAction(action: PairAction): void {
  _activeAction = action;
  document.querySelectorAll<HTMLButtonElement>('.rs-tab').forEach(btn => {
    const isActive = btn.dataset.action === action;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-selected', String(isActive));
  });
  const hint = document.getElementById('rs-hint');
  if (hint) hint.textContent = ACTIONS[action].description;
}

// ---------------------------------------------------------------------------
// Selection watcher — updates context label in real time
// ---------------------------------------------------------------------------

function startSelectionWatcher(): void {
  setInterval(() => {
    const label = document.getElementById('rs-context-label');
    if (!label) return;
    const sel = getSelectedCode();
    const path = getCurrentFilePath();
    if (sel) {
      const lines = sel.split('\n').length;
      label.textContent = `${lines} line${lines !== 1 ? 's' : ''} selected${path ? ` · ${path.split('/').pop()}` : ''}`;
      label.classList.add('has-selection');
    } else {
      label.textContent = path
        ? `No selection — using ${path.split('/').pop()}`
        : 'No selection — using full file';
      label.classList.remove('has-selection');
    }
  }, 500);
}

// ---------------------------------------------------------------------------
// Run action
// ---------------------------------------------------------------------------

async function runAction(): Promise<void> {
  if (_streaming) return;

  const cfg = ACTIONS[_activeAction];
  const code = getSelectedCode() ?? (cfg.requiresSelection ? null : getEditorContent());

  if (!code) {
    showError('Select code in the editor first, then press Run.');
    return;
  }

  _lastCode = code;
  _lastResponse = '';
  setStreaming(true);
  clearResponse();
  showStreamingPlaceholder();

  try {
    _abortController = new AbortController();
    const res = await fetch(GAIA_STREAM_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: _activeAction,
        code,
        file_path: getCurrentFilePath(),
      }),
      signal: _abortController.signal,
    });

    if (!res.ok || !res.body) {
      throw new Error(`GAIA API error: ${res.status}`);
    }

    await streamResponse(res.body);
  } catch (err) {
    if ((err as Error).name !== 'AbortError') {
      showError(`GAIA is unavailable: ${(err as Error).message}`);
    }
  } finally {
    setStreaming(false);
  }
}

// ---------------------------------------------------------------------------
// SSE streaming
// ---------------------------------------------------------------------------

async function streamResponse(body: ReadableStream<Uint8Array>): Promise<void> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  const responseEl = document.getElementById('rs-response');
  if (!responseEl) return;

  clearResponse();

  const pre = document.createElement('pre');
  pre.className = 'rs-code-block streaming';
  const code = document.createElement('code');
  pre.appendChild(code);
  responseEl.appendChild(pre);

  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() ?? '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const chunk = line.slice(6);
        if (chunk === '[DONE]') break;
        _lastResponse += chunk;
        code.textContent = _lastResponse;
        responseEl.scrollTop = responseEl.scrollHeight;
      }
    }
  }

  pre.classList.remove('streaming');
  renderActionButtons(responseEl);
}

// ---------------------------------------------------------------------------
// Action buttons (copy / insert)
// ---------------------------------------------------------------------------

function renderActionButtons(container: HTMLElement): void {
  const existing = container.querySelector('.rs-action-row');
  if (existing) existing.remove();

  const row = document.createElement('div');
  row.className = 'rs-action-row';

  const copyBtn = document.createElement('button');
  copyBtn.className = 'rs-action-btn';
  copyBtn.textContent = '📋 Copy';
  copyBtn.addEventListener('click', async () => {
    await navigator.clipboard.writeText(_lastResponse);
    copyBtn.textContent = '✅ Copied!';
    setTimeout(() => { copyBtn.textContent = '📋 Copy'; }, 2000);
  });

  const insertBtn = document.createElement('button');
  insertBtn.className = 'rs-action-btn rs-action-btn--primary';
  insertBtn.textContent = '⬇ Insert at cursor';
  insertBtn.addEventListener('click', () => {
    insertAtCursor(_lastResponse);
    insertBtn.textContent = '✅ Inserted!';
    setTimeout(() => { insertBtn.textContent = '⬇ Insert at cursor'; }, 2000);
  });

  if (_activeAction !== 'explain') {
    row.appendChild(insertBtn);
  }
  row.appendChild(copyBtn);
  container.appendChild(row);
}

// ---------------------------------------------------------------------------
// UI helpers
// ---------------------------------------------------------------------------

function setStreaming(active: boolean): void {
  _streaming = active;
  const runBtn = document.getElementById('rs-run') as HTMLButtonElement | null;
  const stopBtn = document.getElementById('rs-stop') as HTMLButtonElement | null;
  if (runBtn) { runBtn.disabled = active; runBtn.textContent = active ? '…' : '▶ Run'; }
  if (stopBtn) stopBtn.style.display = active ? 'inline-flex' : 'none';
}

function stopStreaming(): void {
  _abortController?.abort();
  setStreaming(false);
  const responseEl = document.getElementById('rs-response');
  if (responseEl && _lastResponse) renderActionButtons(responseEl);
}

function clearResponse(): void {
  const el = document.getElementById('rs-response');
  if (el) el.innerHTML = '';
}

function showStreamingPlaceholder(): void {
  const el = document.getElementById('rs-response');
  if (!el) return;
  el.innerHTML = '<div class="rs-streaming-cursor"></div>';
}

function showError(msg: string): void {
  const el = document.getElementById('rs-response');
  if (!el) return;
  el.innerHTML = `<div class="rs-error">⚠ ${msg}</div>`;
}

// Suppress unused variable warning — _lastCode is reserved for future
// context-aware features (diff view, history).
void _lastCode;
