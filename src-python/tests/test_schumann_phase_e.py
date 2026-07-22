# Copyright (c) 2026 Kyle Alexander Steen (R0GV3 The Alchemist). All Rights Reserved.
# NEXUS Schumann Sync Engine — Phase E operational test suite
# Tests: sensor simulation, SyncReading physics, SyncPulse tick loop,
#        alignment scoring, state accumulation, Ledger integration.

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from schumann.sync_pulse import (
    ALIGNMENT_TOLERANCE_HZ,
    SCHUMANN_FUNDAMENTAL_HZ,
    SimulatedSchumannSensor,
    SyncPulse,
    SyncReading,
    SyncState,
)


# ---------------------------------------------------------------------------
# SimulatedSchumannSensor
# ---------------------------------------------------------------------------

class TestSimulatedSchumannSensor:
    def test_returns_sync_reading(self):
        sensor = SimulatedSchumannSensor()
        r = sensor.read()
        assert isinstance(r, SyncReading)

    def test_frequency_near_fundamental(self):
        sensor = SimulatedSchumannSensor()
        for _ in range(20):
            r = sensor.read()
            # Frequency must stay within physical drift range
            assert 6.0 <= r.frequency_hz <= 10.0

    def test_coherence_bounded(self):
        sensor = SimulatedSchumannSensor()
        for _ in range(20):
            r = sensor.read()
            assert 0.0 <= r.coherence <= 1.0

    def test_amplitude_bounded(self):
        sensor = SimulatedSchumannSensor()
        for _ in range(20):
            r = sensor.read()
            assert 0.0 <= r.amplitude <= 1.0

    def test_source_is_simulated(self):
        r = SimulatedSchumannSensor().read()
        assert r.source == "simulated"

    def test_harmonic_profile_five_entries(self):
        r = SimulatedSchumannSensor().read()
        assert len(r.harmonic_profile) == 5


# ---------------------------------------------------------------------------
# SyncReading properties
# ---------------------------------------------------------------------------

class TestSyncReading:
    def _make(self, freq: float, coherence: float) -> SyncReading:
        return SyncReading(
            frequency_hz=freq,
            amplitude=0.7,
            coherence=coherence,
            phase_offset_rad=0.0,
            timestamp="2026-07-22T21:20:00+00:00",
            source="test",
        )

    def test_in_band_true_at_fundamental(self):
        r = self._make(SCHUMANN_FUNDAMENTAL_HZ, 0.8)
        assert r.in_band is True

    def test_in_band_true_within_tolerance(self):
        r = self._make(SCHUMANN_FUNDAMENTAL_HZ + ALIGNMENT_TOLERANCE_HZ - 0.01, 0.8)
        assert r.in_band is True

    def test_in_band_false_outside_tolerance(self):
        r = self._make(SCHUMANN_FUNDAMENTAL_HZ + ALIGNMENT_TOLERANCE_HZ + 0.1, 0.8)
        assert r.in_band is False

    def test_alignment_score_perfect(self):
        r = self._make(SCHUMANN_FUNDAMENTAL_HZ, 1.0)
        assert r.alignment_score == 1.0

    def test_alignment_score_zero_out_of_band(self):
        r = self._make(SCHUMANN_FUNDAMENTAL_HZ + ALIGNMENT_TOLERANCE_HZ + 1.0, 1.0)
        assert r.alignment_score == 0.0

    def test_alignment_score_scales_with_coherence(self):
        r_high = self._make(SCHUMANN_FUNDAMENTAL_HZ, 1.0)
        r_low = self._make(SCHUMANN_FUNDAMENTAL_HZ, 0.5)
        assert r_high.alignment_score > r_low.alignment_score

    def test_to_dict_keys(self):
        r = self._make(7.83, 0.9)
        d = r.to_dict()
        for key in ("frequency_hz", "amplitude", "coherence", "alignment_score",
                    "in_band", "high_coherence", "timestamp", "source"):
            assert key in d

    def test_high_coherence_flag(self):
        assert self._make(7.83, 0.5).high_coherence is True
        assert self._make(7.83, 0.1).high_coherence is False


# ---------------------------------------------------------------------------
# SyncState
# ---------------------------------------------------------------------------

class TestSyncState:
    def test_mean_alignment_zero_on_empty(self):
        s = SyncState()
        assert s.mean_alignment_score == 0.0

    def test_in_band_ratio_zero_on_empty(self):
        s = SyncState()
        assert s.in_band_ratio == 0.0

    def test_accumulates_correctly(self):
        s = SyncState()
        s.tick_count = 4
        s.in_band_count = 3
        s.running_alignment_sum = 3.0
        assert s.mean_alignment_score == 0.75
        assert s.in_band_ratio == 0.75


# ---------------------------------------------------------------------------
# SyncPulse — synchronous tick tests (no threading)
# ---------------------------------------------------------------------------

class TestSyncPulseTick:
    def test_single_tick_returns_reading(self):
        engine = SyncPulse(tick_interval_s=60.0)
        r = engine.tick()
        assert isinstance(r, SyncReading)

    def test_state_increments_on_tick(self):
        engine = SyncPulse(tick_interval_s=60.0)
        engine.tick()
        engine.tick()
        assert engine.state.tick_count == 2

    def test_subscriber_called_on_tick(self):
        calls: list[tuple] = []
        engine = SyncPulse(tick_interval_s=60.0)
        engine.subscribe(lambda r, s: calls.append((r, s)))
        engine.tick()
        assert len(calls) == 1
        assert isinstance(calls[0][0], SyncReading)

    def test_multiple_subscribers(self):
        count = [0]
        engine = SyncPulse(tick_interval_s=60.0)
        engine.subscribe(lambda r, s: count.__setitem__(0, count[0] + 1))
        engine.subscribe(lambda r, s: count.__setitem__(0, count[0] + 1))
        engine.tick()
        assert count[0] == 2

    def test_state_last_reading_set(self):
        engine = SyncPulse(tick_interval_s=60.0)
        r = engine.tick()
        assert engine.state.last_reading is r

    def test_in_band_count_non_negative(self):
        engine = SyncPulse(tick_interval_s=60.0)
        for _ in range(10):
            engine.tick()
        assert 0 <= engine.state.in_band_count <= 10


# ---------------------------------------------------------------------------
# SyncPulse — background thread tests
# ---------------------------------------------------------------------------

class TestSyncPulseThread:
    def test_starts_and_stops(self):
        engine = SyncPulse(tick_interval_s=0.05)
        engine.start()
        assert engine.is_running
        time.sleep(0.2)
        engine.stop(timeout=2.0)
        assert not engine.is_running

    def test_multiple_ticks_in_thread(self):
        engine = SyncPulse(tick_interval_s=0.05)
        engine.start()
        time.sleep(0.35)
        engine.stop(timeout=2.0)
        assert engine.state.tick_count >= 3

    def test_double_start_safe(self):
        engine = SyncPulse(tick_interval_s=0.05)
        engine.start()
        engine.start()  # should not raise or spawn second thread
        engine.stop(timeout=2.0)


# ---------------------------------------------------------------------------
# SyncPulse — Planetary Ledger integration
# ---------------------------------------------------------------------------

class TestSyncPulseLedgerIntegration:
    def test_ledger_append_called_on_tick(self):
        mock_ledger = MagicMock()
        engine = SyncPulse(tick_interval_s=60.0, ledger=mock_ledger, session_id="s-001")
        engine.tick()
        mock_ledger.append.assert_called_once()
        call_kwargs = mock_ledger.append.call_args
        assert call_kwargs.kwargs.get("session_id") == "s-001" or \
               (call_kwargs.args and "s-001" in str(call_kwargs))

    def test_ledger_receives_schumann_sync_type(self):
        from planetary_ledger import EventType
        mock_ledger = MagicMock()
        engine = SyncPulse(tick_interval_s=60.0, ledger=mock_ledger)
        engine.tick()
        call_kwargs = mock_ledger.append.call_args.kwargs
        assert call_kwargs["event_type"] == EventType.SCHUMANN_SYNC

    def test_ledger_payload_contains_frequency(self):
        mock_ledger = MagicMock()
        engine = SyncPulse(tick_interval_s=60.0, ledger=mock_ledger)
        engine.tick()
        payload = mock_ledger.append.call_args.kwargs["payload"]
        assert "frequency_hz" in payload
        assert "alignment_score" in payload

    def test_no_ledger_runs_cleanly(self):
        engine = SyncPulse(tick_interval_s=60.0, ledger=None)
        r = engine.tick()  # should not raise
        assert r is not None
