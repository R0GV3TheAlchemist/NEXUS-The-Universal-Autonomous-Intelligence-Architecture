/**
 * src/hooks/useScoreHistory.ts
 * GAIA-OS — Alignment Score History Hook
 * Issue #68 Phase 5
 *
 * Maintains a rolling circular buffer of alignment score snapshots.
 * New readings are appended each time the AlignmentState updates;
 * the buffer is capped at MAX_ENTRIES (default 60 — 30 min at the
 * 30-second poll cadence).
 *
 * Derived stats are recomputed only when the buffer changes so
 * consumers don’t pay for recalculation on every render.
 *
 * Usage:
 *   const history = useScoreHistory(state);
 *   // history.scores       — number[]  (0-100, newest last)
 *   // history.trendDir     — 'rising' | 'falling' | 'stable'
 *   // history.sessionAvg   — number
 */

import { useRef, useState, useEffect } from 'react';
import type { AlignmentState, AlignmentTier } from './useAlignment';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ScoreEntry {
  score:          number;
  hrv_score:      number;
  schumann_score: number;
  solar_kp:       number;
  tier:           AlignmentTier;
  ts:             number;  // Date.now() at capture time
}

export type TrendDirection = 'rising' | 'falling' | 'stable';

export interface ScoreHistory {
  entries:        ScoreEntry[];   // full buffer, newest last
  scores:         number[];       // overall score[] for sparkline
  hrvScores:      number[];       // hrv_score[] for sub-chart
  schumannScores: number[];       // schumann_score[] for sub-chart
  sessionMin:     number;
  sessionMax:     number;
  sessionAvg:     number;
  trendDir:       TrendDirection;
  count:          number;         // total readings captured this session
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const MAX_ENTRIES    = 60;   // 30 minutes at 30 s polling
const TREND_WINDOW   = 6;    // last N readings for trend direction
const TREND_THRESH   = 3;    // minimum delta to call rising/falling

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function computeStats(entries: ScoreEntry[]): Omit<ScoreHistory, 'entries' | 'count'> {
  if (entries.length === 0) {
    return {
      scores:         [],
      hrvScores:      [],
      schumannScores: [],
      sessionMin:     0,
      sessionMax:     0,
      sessionAvg:     0,
      trendDir:       'stable',
    };
  }

  const scores         = entries.map(e => e.score);
  const hrvScores      = entries.map(e => e.hrv_score);
  const schumannScores = entries.map(e => e.schumann_score);

  const sessionMin = Math.min(...scores);
  const sessionMax = Math.max(...scores);
  const sessionAvg = Math.round(scores.reduce((s, v) => s + v, 0) / scores.length);

  // Trend: compare average of last TREND_WINDOW readings vs previous window
  let trendDir: TrendDirection = 'stable';
  if (entries.length >= TREND_WINDOW * 2) {
    const recent = scores.slice(-TREND_WINDOW);
    const prior  = scores.slice(-(TREND_WINDOW * 2), -TREND_WINDOW);
    const recentAvg = recent.reduce((s, v) => s + v, 0) / recent.length;
    const priorAvg  = prior.reduce((s, v)  => s + v, 0) / prior.length;
    const delta = recentAvg - priorAvg;
    if (delta > TREND_THRESH)       trendDir = 'rising';
    else if (delta < -TREND_THRESH) trendDir = 'falling';
  }

  return { scores, hrvScores, schumannScores, sessionMin, sessionMax, sessionAvg, trendDir };
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useScoreHistory(state: AlignmentState | null): ScoreHistory {
  const bufferRef = useRef<ScoreEntry[]>([]);
  const countRef  = useRef(0);
  const prevTs    = useRef<string | null>(null);

  const [history, setHistory] = useState<ScoreHistory>({
    entries:        [],
    scores:         [],
    hrvScores:      [],
    schumannScores: [],
    sessionMin:     0,
    sessionMax:     0,
    sessionAvg:     0,
    trendDir:       'stable',
    count:          0,
  });

  useEffect(() => {
    if (!state) return;
    // Deduplicate: only append if last_updated changed
    if (state.last_updated === prevTs.current) return;
    prevTs.current = state.last_updated;

    const entry: ScoreEntry = {
      score:          state.score,
      hrv_score:      state.hrv_score,
      schumann_score: state.schumann_score,
      solar_kp:       state.solar_kp,
      tier:           state.ui_tier,
      ts:             Date.now(),
    };

    // Append and cap buffer
    const buf = bufferRef.current;
    buf.push(entry);
    if (buf.length > MAX_ENTRIES) buf.shift();
    countRef.current += 1;

    setHistory({
      entries: [...buf],
      count:   countRef.current,
      ...computeStats(buf),
    });
  }, [state?.last_updated]);

  return history;
}
