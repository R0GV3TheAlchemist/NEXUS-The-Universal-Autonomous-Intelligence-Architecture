/**
 * test_viriditas_theme.ts — Vitest unit tests for ViriditasTheme (Issue #68)
 *
 * Tests:
 *   1. classifyTier() boundary cases across the full score range
 *   2. Storm (disturbed) override forces MINIMAL regardless of score
 *   3. Unavailable disturbance falls through to score-based classification
 *   4. Score clamping (out-of-range values)
 */

import { describe, it, expect } from 'vitest';
import { classifyTier, AlignmentTier } from '../src/gaian/ViriditasTheme';

describe('classifyTier — score boundaries', () => {
  it('returns MINIMAL at score 0.0', () => {
    expect(classifyTier(0.0, 'stable')).toBe(AlignmentTier.MINIMAL);
  });

  it('returns MINIMAL at score 0.25', () => {
    expect(classifyTier(0.25, 'stable')).toBe(AlignmentTier.MINIMAL);
  });

  it('returns CORE at score 0.26', () => {
    expect(classifyTier(0.26, 'stable')).toBe(AlignmentTier.CORE);
  });

  it('returns CORE at score 0.45', () => {
    expect(classifyTier(0.45, 'stable')).toBe(AlignmentTier.CORE);
  });

  it('returns STANDARD at score 0.46', () => {
    expect(classifyTier(0.46, 'stable')).toBe(AlignmentTier.STANDARD);
  });

  it('returns STANDARD at score 0.65', () => {
    expect(classifyTier(0.65, 'stable')).toBe(AlignmentTier.STANDARD);
  });

  it('returns FULL at score 0.66', () => {
    expect(classifyTier(0.66, 'stable')).toBe(AlignmentTier.FULL);
  });

  it('returns FULL at score 0.84', () => {
    expect(classifyTier(0.84, 'stable')).toBe(AlignmentTier.FULL);
  });

  it('returns VIBRANT at score 0.85', () => {
    expect(classifyTier(0.85, 'stable')).toBe(AlignmentTier.VIBRANT);
  });

  it('returns VIBRANT at score 1.0', () => {
    expect(classifyTier(1.0, 'stable')).toBe(AlignmentTier.VIBRANT);
  });
});

describe('classifyTier — storm override', () => {
  it('forces MINIMAL when disturbed, even at high score (Kp > 8 scenario)', () => {
    expect(classifyTier(0.92, 'disturbed')).toBe(AlignmentTier.MINIMAL);
  });

  it('forces MINIMAL when disturbed at mid score', () => {
    expect(classifyTier(0.55, 'disturbed')).toBe(AlignmentTier.MINIMAL);
  });

  it('forces MINIMAL when disturbed at low score', () => {
    expect(classifyTier(0.10, 'disturbed')).toBe(AlignmentTier.MINIMAL);
  });
});

describe('classifyTier — unavailable signal', () => {
  it('falls through to score-based classification when unavailable', () => {
    // Unavailable ≠ disturbed; score-based logic applies
    expect(classifyTier(0.72, 'unavailable')).toBe(AlignmentTier.FULL);
  });

  it('returns MINIMAL when unavailable and score is low', () => {
    expect(classifyTier(0.18, 'unavailable')).toBe(AlignmentTier.MINIMAL);
  });
});

describe('classifyTier — elevated disturbance', () => {
  it('does NOT override tier at elevated disturbance (score wins)', () => {
    expect(classifyTier(0.78, 'elevated')).toBe(AlignmentTier.FULL);
  });
});

describe('classifyTier — score clamping', () => {
  it('clamps negative scores to MINIMAL', () => {
    expect(classifyTier(-0.5, 'stable')).toBe(AlignmentTier.MINIMAL);
  });

  it('clamps scores > 1.0 to VIBRANT', () => {
    expect(classifyTier(1.5, 'stable')).toBe(AlignmentTier.VIBRANT);
  });
});
