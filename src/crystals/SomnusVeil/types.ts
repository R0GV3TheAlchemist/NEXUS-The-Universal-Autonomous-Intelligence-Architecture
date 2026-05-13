/**
 * SomnusVeil — Sleep, Dream & Rest Intelligence Crystal
 *
 * Tracks sleep context, dream entries, and rest state.
 * GAIA adjusts tone and energy level based on the user's declared rest state.
 */

export type RestState =
  | 'rested'      // Slept well, feeling restored
  | 'neutral'     // Okay, neither rested nor drained
  | 'tired'       // Noticeably low energy
  | 'exhausted'   // Running on empty
  | 'recovering'; // Post-illness, post-stress recovery

export const REST_STATE_ICON: Record<RestState, string> = {
  rested:     '🌕',
  neutral:    '🌔',
  tired:      '🌓',
  exhausted:  '🌑',
  recovering: '🌒',
};

export const REST_STATE_LABEL: Record<RestState, string> = {
  rested:     'Rested',
  neutral:    'Neutral',
  tired:      'Tired',
  exhausted:  'Exhausted',
  recovering: 'Recovering',
};

/** GAIA tone modifier returned alongside RestState — used by chat context. */
export const REST_STATE_TONE: Record<RestState, string> = {
  rested:     'energised and expansive',
  neutral:    'balanced and clear',
  tired:      'gentle and concise',
  exhausted:  'very gentle, minimal, supportive',
  recovering: 'warm, slow, nurturing',
};

export type SleepQuality = 1 | 2 | 3 | 4 | 5;

export interface SleepEntry {
  id: string;
  date: string;           // ISO date string YYYY-MM-DD
  bedtime: string;        // HH:MM (24h)
  wakeTime: string;       // HH:MM (24h)
  durationHours: number;  // Computed from bed/wake
  quality: SleepQuality;  // 1–5 stars
  note: string;
  timestamp: number;      // Unix ms of entry creation
}

export type DreamTone =
  | 'vivid'
  | 'peaceful'
  | 'unsettling'
  | 'lucid'
  | 'fragmented'
  | 'symbolic';

export const DREAM_TONE_ICON: Record<DreamTone, string> = {
  vivid:       '✦',
  peaceful:    '◇',
  unsettling:  '◈',
  lucid:       '◉',
  fragmented:  '◌',
  symbolic:    '◆',
};

export interface DreamEntry {
  id: string;
  date: string;           // ISO date string
  title: string;          // Short user-given title
  content: string;        // Dream description
  tone: DreamTone;
  tags: string[];         // e.g. ['water', 'flight', 'shadow']
  timestamp: number;
}

export interface SomnusVeilState {
  currentRestState: RestState;
  sleepLog: SleepEntry[];
  dreamJournal: DreamEntry[];
  /** Rolling 7-day average sleep duration */
  weekAvgHours: number;
  /** Rolling 7-day average sleep quality */
  weekAvgQuality: number;
  /** Most recent sleep entry */
  lastSleep: SleepEntry | null;
  /** Most recent dream entry */
  lastDream: DreamEntry | null;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

export function parseDurationHours(bedtime: string, wakeTime: string): number {
  const [bh, bm] = bedtime.split(':').map(Number);
  const [wh, wm] = wakeTime.split(':').map(Number);
  let bedMins = bh * 60 + bm;
  let wakeMins = wh * 60 + wm;
  if (wakeMins <= bedMins) wakeMins += 24 * 60; // crosses midnight
  return Math.round(((wakeMins - bedMins) / 60) * 10) / 10;
}

export function qualityStars(q: SleepQuality): string {
  return '★'.repeat(q) + '☆'.repeat(5 - q);
}

export function todayISO(): string {
  return new Date().toISOString().slice(0, 10);
}
