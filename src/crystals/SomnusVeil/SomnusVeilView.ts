/**
 * SomnusVeilView
 * Full UI panel for the SomnusVeil crystal.
 *
 * Layout:
 *   ┌──────────────────────────────────────┐
 *   │  Rest state selector (moon phases)   │
 *   ├──────────────────────────────────────┤
 *   │  Weekly stats: avg hours / quality   │
 *   ├──────────────────────────────────────┤
 *   │  Tabs: [Sleep Log] [Dream Journal]   │
 *   ├──────────────────────────────────────┤
 *   │  Active tab content + entry form     │
 *   └──────────────────────────────────────┘
 */

import {
  subscribe,
  setRestState,
  logSleep,
  logDream,
  getSomnus,
} from './store';
import {
  REST_STATE_ICON,
  REST_STATE_LABEL,
  REST_STATE_TONE,
  DREAM_TONE_ICON,
  qualityStars,
  type SomnusVeilState,
  type SleepEntry,
  type DreamEntry,
  type RestState,
  type DreamTone,
  type SleepQuality,
} from './types';

const REST_STATES: RestState[] = [
  'rested', 'neutral', 'tired', 'exhausted', 'recovering',
];

const DREAM_TONES: DreamTone[] = [
  'vivid', 'peaceful', 'unsettling', 'lucid', 'fragmented', 'symbolic',
];

export class SomnusVeilView {
  private _root: HTMLElement;
  private _unsub: (() => void) | null = null;

  // Tab state
  private _activeTab: 'sleep' | 'dream' = 'sleep';

  // Sleep form state
  private _bedtime = '22:30';
  private _wakeTime = '07:00';
  private _quality: SleepQuality = 3;
  private _sleepNote = '';

  // Dream form state
  private _dreamTitle = '';
  private _dreamContent = '';
  private _dreamTone: DreamTone = 'vivid';
  private _dreamTags = '';

  constructor(container: HTMLElement) {
    this._root = document.createElement('div');
    this._root.className = 'sv-panel';
    container.appendChild(this._root);

    this._render(getSomnus());
    this._unsub = subscribe((state) => this._render(state));
  }

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  private _render(state: SomnusVeilState): void {
    const { currentRestState, weekAvgHours, weekAvgQuality } = state;
    const tone = REST_STATE_TONE[currentRestState];

    this._root.innerHTML = /* html */ `
      <!-- Rest State Selector -->
      <div class="sv-rest-row" role="group" aria-label="Current rest state">
        ${REST_STATES.map((rs) => /* html */ `
          <button class="sv-rest-btn ${currentRestState === rs ? 'sv-rest-btn--active' : ''}"
            data-rest="${rs}" title="${REST_STATE_LABEL[rs]}" aria-pressed="${currentRestState === rs}">
            <span class="sv-moon">${REST_STATE_ICON[rs]}</span>
            <span class="sv-rest-label">${REST_STATE_LABEL[rs]}</span>
          </button>`).join('')}
      </div>
      <p class="sv-tone-hint">GAIA tone: <em>${_esc(tone)}</em></p>

      <!-- Weekly Stats -->
      <div class="sv-stats-row">
        <div class="sv-stat">
          <span class="sv-stat-value">${weekAvgHours || '—'}</span>
          <span class="sv-stat-label">avg hrs / night</span>
        </div>
        <div class="sv-stat">
          <span class="sv-stat-value">${weekAvgQuality ? weekAvgQuality.toFixed(1) : '—'}</span>
          <span class="sv-stat-label">avg quality</span>
        </div>
        <div class="sv-stat">
          <span class="sv-stat-value">${state.sleepLog.length}</span>
          <span class="sv-stat-label">nights logged</span>
        </div>
        <div class="sv-stat">
          <span class="sv-stat-value">${state.dreamJournal.length}</span>
          <span class="sv-stat-label">dreams recorded</span>
        </div>
      </div>

      <!-- Tabs -->
      <div class="sv-tabs" role="tablist">
        <button class="sv-tab ${this._activeTab === 'sleep' ? 'sv-tab--active' : ''}"
          data-tab="sleep" role="tab" aria-selected="${this._activeTab === 'sleep'}">🌙 Sleep Log</button>
        <button class="sv-tab ${this._activeTab === 'dream' ? 'sv-tab--active' : ''}"
          data-tab="dream" role="tab" aria-selected="${this._activeTab === 'dream'}">✦ Dream Journal</button>
      </div>

      <!-- Tab Content -->
      <div class="sv-tab-content">
        ${this._activeTab === 'sleep'
          ? this._renderSleepTab(state)
          : this._renderDreamTab(state)}
      </div>
    `;

    this._bindEvents();
  }

  // -------------------------------------------------------------------------
  // Sleep tab
  // -------------------------------------------------------------------------

  private _renderSleepTab(state: SomnusVeilState): string {
    return /* html */ `
      <form class="sv-form" id="sv-sleep-form" aria-label="Log sleep">
        <div class="sv-form-row">
          <div class="sv-field">
            <label for="sv-bedtime">Bedtime</label>
            <input id="sv-bedtime" type="time" value="${this._bedtime}" class="sv-input"/>
          </div>
          <div class="sv-field">
            <label for="sv-wake">Wake time</label>
            <input id="sv-wake" type="time" value="${this._wakeTime}" class="sv-input"/>
          </div>
        </div>
        <div class="sv-quality-row">
          <span class="sv-quality-label">Quality</span>
          ${([1,2,3,4,5] as SleepQuality[]).map((q) => /* html */ `
            <button type="button" class="sv-star ${this._quality >= q ? 'sv-star--lit' : ''}"
              data-q="${q}" aria-label="Quality ${q}">★</button>`).join('')}
        </div>
        <input id="sv-sleep-note" type="text" placeholder="Any notes about this sleep?"
          value="${_esc(this._sleepNote)}" class="sv-input sv-input--full" maxlength="200"/>
        <button type="submit" class="sv-submit-btn">Log Sleep</button>
      </form>

      <div class="sv-entry-list">
        ${state.sleepLog.slice(0, 14).map(_sleepRow).join('') ||
          '<p class="sv-empty">No sleep entries yet.</p>'}
      </div>
    `;
  }

  // -------------------------------------------------------------------------
  // Dream tab
  // -------------------------------------------------------------------------

  private _renderDreamTab(state: SomnusVeilState): string {
    return /* html */ `
      <form class="sv-form" id="sv-dream-form" aria-label="Log dream">
        <input id="sv-dream-title" type="text" placeholder="Dream title…"
          value="${_esc(this._dreamTitle)}" class="sv-input sv-input--full" maxlength="100"/>
        <textarea id="sv-dream-content" placeholder="Describe the dream…"
          class="sv-textarea" rows="3" maxlength="2000">${_esc(this._dreamContent)}</textarea>
        <div class="sv-tone-row">
          <span class="sv-tone-label">Tone</span>
          ${DREAM_TONES.map((t) => /* html */ `
            <button type="button"
              class="sv-tone-btn ${this._dreamTone === t ? 'sv-tone-btn--active' : ''}"
              data-tone="${t}" title="${t}">${DREAM_TONE_ICON[t]} ${t}</button>`).join('')}
        </div>
        <input id="sv-dream-tags" type="text" placeholder="Tags (comma separated): water, flight…"
          value="${_esc(this._dreamTags)}" class="sv-input sv-input--full" maxlength="200"/>
        <button type="submit" class="sv-submit-btn">Record Dream</button>
      </form>

      <div class="sv-entry-list">
        ${state.dreamJournal.slice(0, 10).map(_dreamCard).join('') ||
          '<p class="sv-empty">No dream entries yet. Record your first dream above.</p>'}
      </div>
    `;
  }

  // -------------------------------------------------------------------------
  // Event binding
  // -------------------------------------------------------------------------

  private _bindEvents(): void {
    const root = this._root;

    // Rest state buttons
    root.querySelectorAll<HTMLButtonElement>('.sv-rest-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        setRestState(btn.dataset.rest as RestState);
      });
    });

    // Tabs
    root.querySelectorAll<HTMLButtonElement>('.sv-tab').forEach((btn) => {
      btn.addEventListener('click', () => {
        this._activeTab = btn.dataset.tab as 'sleep' | 'dream';
        this._render(getSomnus());
      });
    });

    if (this._activeTab === 'sleep') {
      this._bindSleepForm();
    } else {
      this._bindDreamForm();
    }
  }

  private _bindSleepForm(): void {
    const root = this._root;

    root.querySelector<HTMLInputElement>('#sv-bedtime')?.addEventListener('change', (e) => {
      this._bedtime = (e.target as HTMLInputElement).value;
    });
    root.querySelector<HTMLInputElement>('#sv-wake')?.addEventListener('change', (e) => {
      this._wakeTime = (e.target as HTMLInputElement).value;
    });
    root.querySelector<HTMLInputElement>('#sv-sleep-note')?.addEventListener('input', (e) => {
      this._sleepNote = (e.target as HTMLInputElement).value;
    });

    // Star quality
    root.querySelectorAll<HTMLButtonElement>('.sv-star').forEach((btn) => {
      btn.addEventListener('click', () => {
        this._quality = Number(btn.dataset.q) as SleepQuality;
        root.querySelectorAll('.sv-star').forEach((s, i) => {
          s.classList.toggle('sv-star--lit', i < this._quality);
        });
      });
    });

    root.querySelector<HTMLFormElement>('#sv-sleep-form')?.addEventListener('submit', (e) => {
      e.preventDefault();
      logSleep(this._bedtime, this._wakeTime, this._quality, this._sleepNote);
      this._sleepNote = '';
    });
  }

  private _bindDreamForm(): void {
    const root = this._root;

    root.querySelector<HTMLInputElement>('#sv-dream-title')?.addEventListener('input', (e) => {
      this._dreamTitle = (e.target as HTMLInputElement).value;
    });
    root.querySelector<HTMLTextAreaElement>('#sv-dream-content')?.addEventListener('input', (e) => {
      this._dreamContent = (e.target as HTMLTextAreaElement).value;
    });
    root.querySelector<HTMLInputElement>('#sv-dream-tags')?.addEventListener('input', (e) => {
      this._dreamTags = (e.target as HTMLInputElement).value;
    });

    // Tone selector
    root.querySelectorAll<HTMLButtonElement>('.sv-tone-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        this._dreamTone = btn.dataset.tone as DreamTone;
        root.querySelectorAll('.sv-tone-btn').forEach((b) =>
          b.classList.toggle('sv-tone-btn--active', b === btn),
        );
      });
    });

    root.querySelector<HTMLFormElement>('#sv-dream-form')?.addEventListener('submit', (e) => {
      e.preventDefault();
      const title = this._dreamTitle.trim();
      const content = this._dreamContent.trim();
      if (!title && !content) return;
      const tags = this._dreamTags
        .split(',')
        .map((t) => t.trim())
        .filter(Boolean);
      logDream(title || 'Untitled dream', content, this._dreamTone, tags);
      this._dreamTitle = '';
      this._dreamContent = '';
      this._dreamTags = '';
    });
  }

  // -------------------------------------------------------------------------
  // Lifecycle
  // -------------------------------------------------------------------------

  dispose(): void {
    this._unsub?.();
    this._root.remove();
  }
}

// ---------------------------------------------------------------------------
// Pure helpers
// ---------------------------------------------------------------------------

function _sleepRow(entry: SleepEntry): string {
  const qualityColor =
    entry.quality >= 4
      ? 'var(--color-success)'
      : entry.quality >= 3
      ? 'var(--color-primary)'
      : 'var(--color-warning)';
  return /* html */ `
    <div class="sv-sleep-row">
      <div class="sv-sleep-main">
        <span class="sv-sleep-duration" style="color:${qualityColor}">
          ${entry.durationHours}h
        </span>
        <div class="sv-sleep-times">
          <span>${entry.bedtime} → ${entry.wakeTime}</span>
          <span class="sv-sleep-date">${entry.date}</span>
        </div>
        <span class="sv-sleep-stars" style="color:${qualityColor}">${qualityStars(entry.quality)}</span>
      </div>
      ${entry.note ? `<p class="sv-sleep-note">${_esc(entry.note)}</p>` : ''}
    </div>
  `;
}

function _dreamCard(entry: DreamEntry): string {
  return /* html */ `
    <div class="sv-dream-card">
      <div class="sv-dream-header">
        <span class="sv-dream-tone-icon">${DREAM_TONE_ICON[entry.tone]}</span>
        <span class="sv-dream-title">${_esc(entry.title)}</span>
        <span class="sv-dream-date">${entry.date}</span>
      </div>
      ${entry.content ? /* html */ `
        <p class="sv-dream-content">${_esc(entry.content.slice(0, 200))}${entry.content.length > 200 ? '…' : ''}</p>` : ''}
      ${entry.tags.length > 0 ? /* html */ `
        <div class="sv-dream-tags">
          ${entry.tags.map((t) => `<span class="sv-dream-tag">${_esc(t)}</span>`).join('')}
        </div>` : ''}
    </div>
  `;
}

function _esc(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}
