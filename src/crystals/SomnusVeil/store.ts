/**
 * SomnusVeil Store
 * Sovereign-local sleep & dream state.
 * hydrateFromStorage() ready for DEK ring integration.
 */

import type {
  SleepEntry,
  DreamEntry,
  DreamTone,
  RestState,
  SleepQuality,
  SomnusVeilState,
} from './types';
import { parseDurationHours, todayISO } from './types';

// ---------------------------------------------------------------------------
// Internal state
// ---------------------------------------------------------------------------

let _restState: RestState = 'neutral';
let _sleepLog: SleepEntry[] = [];
let _dreamJournal: DreamEntry[] = [];
let _listeners: Array<(state: SomnusVeilState) => void> = [];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function _uid(prefix: string): string {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;
}

function _avgField(
  entries: SleepEntry[],
  field: 'durationHours' | 'quality',
): number {
  if (entries.length === 0) return 0;
  const sum = entries.reduce((s, e) => s + e[field], 0);
  return Math.round((sum / entries.length) * 10) / 10;
}

function _buildState(): SomnusVeilState {
  const now = Date.now();
  const week = _sleepLog.filter((e) => e.timestamp > now - 7 * 86_400_000);
  const sortedSleep = [..._sleepLog].sort((a, b) => b.timestamp - a.timestamp);
  const sortedDreams = [..._dreamJournal].sort(
    (a, b) => b.timestamp - a.timestamp,
  );
  return {
    currentRestState: _restState,
    sleepLog: sortedSleep,
    dreamJournal: sortedDreams,
    weekAvgHours: _avgField(week, 'durationHours'),
    weekAvgQuality: _avgField(week, 'quality'),
    lastSleep: sortedSleep[0] ?? null,
    lastDream: sortedDreams[0] ?? null,
  };
}

function _notify(): void {
  const state = _buildState();
  _listeners.forEach((fn) => fn(state));
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export function subscribe(
  listener: (state: SomnusVeilState) => void,
): () => void {
  _listeners.push(listener);
  return () => {
    _listeners = _listeners.filter((l) => l !== listener);
  };
}

/** Declare current rest state — GAIA reads this to adapt its tone. */
export function setRestState(state: RestState): void {
  _restState = state;
  _notify();
}

/** Log a sleep session. */
export function logSleep(
  bedtime: string,
  wakeTime: string,
  quality: SleepQuality,
  note = '',
  date = todayISO(),
): SleepEntry {
  const entry: SleepEntry = {
    id: _uid('sv_sleep'),
    date,
    bedtime,
    wakeTime,
    durationHours: parseDurationHours(bedtime, wakeTime),
    quality,
    note,
    timestamp: Date.now(),
  };
  _sleepLog.push(entry);
  _notify();
  return entry;
}

/** Log a dream journal entry. */
export function logDream(
  title: string,
  content: string,
  tone: DreamTone,
  tags: string[] = [],
  date = todayISO(),
): DreamEntry {
  const entry: DreamEntry = {
    id: _uid('sv_dream'),
    date,
    title: title.trim(),
    content: content.trim(),
    tone,
    tags,
    timestamp: Date.now(),
  };
  _dreamJournal.push(entry);
  _notify();
  return entry;
}

/** Return current state snapshot. */
export function getSomnus(): SomnusVeilState {
  return _buildState();
}

/** Reset (tests / onboarding). */
export function resetVeil(): void {
  _restState = 'neutral';
  _sleepLog = [];
  _dreamJournal = [];
  _notify();
}

/** Hydrate from DEK ring storage. */
export function hydrateFromStorage(
  restState: RestState,
  sleepLog: SleepEntry[],
  dreamJournal: DreamEntry[],
): void {
  _restState = restState;
  _sleepLog = sleepLog;
  _dreamJournal = dreamJournal;
  _notify();
}
