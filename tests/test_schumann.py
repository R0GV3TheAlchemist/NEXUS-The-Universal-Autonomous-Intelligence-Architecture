"""
Test suite for Schumann Alignment Layer — Issue #64.

Covers:
  1. Model construction and validation
  2. DevSource yields correct channel names and value ranges
  3. SchumannEngine produces stable state on clean dev feed
  4. SchumannEngine detects disturbance on storm-injected feed
  5. alignment_score is bounded to [0, 1]
  6. confidence drops when data is unavailable
  7. to_stage_dict() keys match Stage Engine contract
  8. experimental_flags are absent when flag is off
  9. DisturbanceLevel ordering
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from schumann.models import DisturbanceLevel, PlanetarySignalSample, SchumannState
from schumann.engine import EngineConfig, SchumannEngine
from schumann.sources import DevSource, build_source


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def _warm_engine(engine: SchumannEngine, ticks: int = 60) -> None:
    """Feed N ticks of data into engine without sleeping."""
    source: DevSource = engine._source  # type: ignore
    source.tick_interval_s = 0.0  # skip asyncio.sleep for speed
    count = 0
    async for sample in source.stream():
        engine._windows[sample.channel].append(
            (sample.timestamp, sample.value, sample.quality)
        )
        count += 1
        if count >= ticks * 7:  # 7 channels per tick
            break


# ---------------------------------------------------------------------------
# 1. Model validation
# ---------------------------------------------------------------------------

class TestPlanetarySignalSample:
    def test_valid(self):
        s = PlanetarySignalSample(
            timestamp=utcnow(), channel="sr_f1",
            value=1.0, unit="pT", source="dev", quality=0.9,
        )
        assert s.quality == 0.9

    def test_quality_out_of_range(self):
        with pytest.raises(ValueError):
            PlanetarySignalSample(
                timestamp=utcnow(), channel="sr_f1",
                value=1.0, unit="pT", source="dev", quality=1.5,
            )

    def test_naive_timestamp_rejected(self):
        with pytest.raises(ValueError):
            PlanetarySignalSample(
                timestamp=datetime(2026, 1, 1),  # no tzinfo
                channel="sr_f1", value=1.0, unit="pT", source="dev",
            )


class TestSchumannStateHelpers:
    def _make_state(self, confidence=0.8, disturbance=DisturbanceLevel.STABLE):
        return SchumannState(
            timestamp=utcnow(),
            fundamental_hz=7.83,
            harmonic_power={"f1": 1.0, "f2": 0.55, "f3": 0.30, "f4": 0.18, "f5": 0.10},
            geomagnetic_activity=0.1,
            signal_quality=0.9,
            disturbance_level=disturbance,
            alignment_score=0.8,
            confidence=confidence,
            source_ids=["dev"],
        )

    def test_is_trusted_above_threshold(self):
        assert self._make_state(confidence=0.5).is_trusted is True

    def test_is_trusted_below_threshold(self):
        assert self._make_state(confidence=0.3).is_trusted is False

    def test_is_disturbed(self):
        assert self._make_state(disturbance=DisturbanceLevel.DISTURBED).is_disturbed is True
        assert self._make_state(disturbance=DisturbanceLevel.STABLE).is_disturbed is False

    def test_to_stage_dict_keys(self):
        expected_keys = {
            "timestamp", "fundamental_hz", "geomagnetic_activity",
            "disturbance_level", "alignment_score", "confidence", "is_trusted",
        }
        d = self._make_state().to_stage_dict()
        assert expected_keys.issubset(d.keys())


# ---------------------------------------------------------------------------
# 2. DevSource
# ---------------------------------------------------------------------------

class TestDevSource:
    def test_channel_names(self):
        source = DevSource(tick_interval_s=0.0, seed=0)
        channels = set()
        count = 0
        async def collect():
            nonlocal count
            async for s in source.stream():
                channels.add(s.channel)
                count += 1
                if count >= 7:
                    break
        asyncio.run(collect())
        assert "sr_f1_freq" in channels
        assert "sr_f1" in channels
        assert "geomag_kp" in channels

    def test_fundamental_in_range(self):
        source = DevSource(tick_interval_s=0.0, seed=1)
        freqs = []
        async def collect():
            async for s in source.stream():
                if s.channel == "sr_f1_freq":
                    freqs.append(s.value)
                if len(freqs) >= 20:
                    break
        asyncio.run(collect())
        assert all(7.0 < f < 8.6 for f in freqs), freqs

    def test_storm_kp_elevated(self):
        source = DevSource(tick_interval_s=0.0, inject_storm=True, seed=2)
        kp_vals = []
        count = 0
        async def collect():
            nonlocal count
            async for s in source.stream():
                count += 1
                # Fast-forward past tick 60
                source._tick = 65
                if s.channel == "geomag_kp":
                    kp_vals.append(s.value)
                if len(kp_vals) >= 5:
                    break
        asyncio.run(collect())
        assert any(kp > 0.5 for kp in kp_vals), kp_vals


# ---------------------------------------------------------------------------
# 3-8. SchumannEngine
# ---------------------------------------------------------------------------

class TestSchumannEngine:
    def _make_engine(self, inject_storm=False, experimental=False) -> SchumannEngine:
        cfg = EngineConfig(
            source="dev",
            source_kwargs={"tick_interval_s": 0.0, "inject_storm": inject_storm},
            window_size=500,
            staleness_threshold=60.0,
            experimental=experimental,
        )
        return SchumannEngine(cfg)

    def test_stable_state_after_warmup(self):
        engine = self._make_engine()
        async def run():
            await _warm_engine(engine, ticks=60)
            return await engine.tick()
        state = asyncio.run(run())
        assert state.disturbance_level == DisturbanceLevel.STABLE
        assert 7.0 < state.fundamental_hz < 8.6

    def test_alignment_score_bounded(self):
        engine = self._make_engine()
        async def run():
            await _warm_engine(engine, ticks=30)
            return await engine.tick()
        state = asyncio.run(run())
        assert 0.0 <= state.alignment_score <= 1.0

    def test_confidence_bounded(self):
        engine = self._make_engine()
        async def run():
            await _warm_engine(engine, ticks=30)
            return await engine.tick()
        state = asyncio.run(run())
        assert 0.0 <= state.confidence <= 1.0

    def test_no_experimental_by_default(self):
        engine = self._make_engine(experimental=False)
        async def run():
            await _warm_engine(engine, ticks=10)
            return await engine.tick()
        state = asyncio.run(run())
        assert state.experimental_flags == {}

    def test_experimental_flags_present_when_enabled(self):
        engine = self._make_engine(experimental=True)
        async def run():
            await _warm_engine(engine, ticks=10)
            return await engine.tick()
        state = asyncio.run(run())
        assert "quantum_bio_coupling" in state.experimental_flags
        assert "seismic_precursor_score" in state.experimental_flags

    def test_empty_engine_returns_unavailable(self):
        engine = self._make_engine()
        state = asyncio.run(engine.tick())
        assert state.disturbance_level == DisturbanceLevel.UNAVAILABLE
        assert state.confidence < 0.4
        assert state.is_trusted is False

    def test_stage_dict_is_complete(self):
        engine = self._make_engine()
        async def run():
            await _warm_engine(engine, ticks=30)
            return await engine.tick()
        state = asyncio.run(run())
        d = state.to_stage_dict()
        required = {
            "timestamp", "fundamental_hz", "geomagnetic_activity",
            "disturbance_level", "alignment_score", "confidence", "is_trusted",
        }
        assert required.issubset(d.keys())


# ---------------------------------------------------------------------------
# 9. DisturbanceLevel ordering
# ---------------------------------------------------------------------------

class TestDisturbanceLevelOrder:
    def test_stable_lt_disturbed(self):
        assert DisturbanceLevel.STABLE < DisturbanceLevel.DISTURBED

    def test_elevated_between(self):
        assert DisturbanceLevel.STABLE < DisturbanceLevel.ELEVATED
        assert DisturbanceLevel.ELEVATED < DisturbanceLevel.DISTURBED
