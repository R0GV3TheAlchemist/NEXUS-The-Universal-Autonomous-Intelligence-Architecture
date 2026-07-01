"""
tests/test_atlas.py
GAIA-APP — Atlas Earth Engine Test Suite

Covers:
  - SchumannReader: frequency model, harmonics, mode classification
  - GeomagneticReader: Kp classification, fallback behavior
  - EarthPulse: data model, computed properties, serialization
  - AtlasEngine: initialization, pulse retrieval, history, status
  - Singleton: get_atlas() idempotency
  - Integration: pulse feeds into Viriditas carrier selection
"""

import math
import time
import pytest
from unittest.mock import patch, MagicMock

import core.atlas as atlas_module

from core.atlas import (
    SchumannReader,
    GeomagneticReader,
    AtlasEngine,
    EarthPulse,
    GeomagneticState,
    SchumannMode,
    AtlasStatus,
    get_atlas,
    SCHUMANN_FUNDAMENTAL,
    KP_QUIET,
    KP_MINOR_STORM,
    KP_MAJOR_STORM,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _inject_requests(side_effect=None, json_data=None):
    """Context manager: inject a fake 'requests' module onto core.atlas.

    Neither patch() nor patch.object() can create a new attribute on a module
    when it does not already exist (Python 3.11 behaviour, requests not installed
    in CI).  We therefore use setattr/delattr directly with try/finally cleanup.

    Usage::

        with _inject_requests(side_effect=Exception("boom")):
            kp = reader.fetch_kp()
    """
    import contextlib

    @contextlib.contextmanager
    def _ctx():
        fake = MagicMock()
        if side_effect is not None:
            fake.get.side_effect = side_effect
        elif json_data is not None:
            mock_resp = MagicMock()
            mock_resp.json.return_value = json_data
            fake.get.return_value = mock_resp

        had_attr = hasattr(atlas_module, "requests")
        original = getattr(atlas_module, "requests", None)
        atlas_module.requests = fake
        try:
            yield fake
        finally:
            if had_attr:
                atlas_module.requests = original
            else:
                try:
                    delattr(atlas_module, "requests")
                except AttributeError:
                    pass

    return _ctx()


# ─────────────────────────────────────────────────────────────────────────────
# SchumannReader Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestSchumannReader:

    def setup_method(self):
        self.reader = SchumannReader()

    def test_read_returns_tuple(self):
        hz, amplitude = self.reader.read()
        assert isinstance(hz, float)
        assert isinstance(amplitude, float)

    def test_hz_within_natural_range(self):
        """Schumann should stay within ±1 Hz of 7.83 under normal conditions."""
        for kp in [0.0, 2.0, 4.0]:
            hz, _ = self.reader.read(kp_index=kp)
            assert 6.5 <= hz <= 9.0, f"Hz {hz} out of natural range at Kp={kp}"

    def test_amplitude_clamped_0_to_1(self):
        for kp in [0.0, 5.0, 9.0]:
            _, amplitude = self.reader.read(kp_index=kp)
            assert 0.0 <= amplitude <= 1.0

    def test_high_kp_reduces_amplitude(self):
        _, amp_quiet = self.reader.read(kp_index=0.0)
        _, amp_storm = self.reader.read(kp_index=9.0)
        assert amp_storm < amp_quiet

    def test_harmonics_count(self):
        harmonics = self.reader.get_harmonics(7.83)
        assert len(harmonics) == 5

    def test_harmonics_ascending(self):
        harmonics = self.reader.get_harmonics(7.83)
        assert harmonics == sorted(harmonics)

    def test_harmonics_first_is_fundamental(self):
        hz = 7.83
        harmonics = self.reader.get_harmonics(hz)
        assert abs(harmonics[0] - hz) < 0.01

    def test_dominant_mode_fundamental(self):
        mode = self.reader.get_dominant_mode(7.83)
        assert mode == SchumannMode.FUNDAMENTAL

    def test_dominant_mode_second(self):
        mode = self.reader.get_dominant_mode(14.3)
        assert mode == SchumannMode.SECOND

    def test_dominant_mode_fifth(self):
        mode = self.reader.get_dominant_mode(33.8)
        assert mode == SchumannMode.FIFTH


# ─────────────────────────────────────────────────────────────────────────────
# GeomagneticReader Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestGeomagneticReader:

    def setup_method(self):
        self.reader = GeomagneticReader()

    def test_classify_quiet(self):
        assert self.reader.classify_kp(1.0) == GeomagneticState.QUIET
        assert self.reader.classify_kp(2.5) == GeomagneticState.QUIET

    def test_classify_unsettled(self):
        assert self.reader.classify_kp(4.0) == GeomagneticState.UNSETTLED

    def test_classify_minor_storm(self):
        assert self.reader.classify_kp(5.0) == GeomagneticState.MINOR_STORM
        assert self.reader.classify_kp(6.5) == GeomagneticState.MINOR_STORM

    def test_classify_major_storm(self):
        assert self.reader.classify_kp(7.0) == GeomagneticState.MAJOR_STORM
        assert self.reader.classify_kp(9.0) == GeomagneticState.MAJOR_STORM

    def test_kp_fallback_no_requests(self):
        """When requests is unavailable, should return default Kp."""
        with patch("core.atlas._REQUESTS_AVAILABLE", False):
            kp = self.reader.fetch_kp()
            assert kp == GeomagneticReader._DEFAULT_KP

    def test_bz_fallback_no_requests(self):
        with patch("core.atlas._REQUESTS_AVAILABLE", False):
            bz = self.reader.fetch_solar_wind_bz()
            assert bz == GeomagneticReader._DEFAULT_BZ

    def test_kp_fallback_on_network_error(self):
        """When requests is 'available' but the network call raises, return default Kp.

        Root cause: atlas.py imports requests inside try/except, so when the
        package is absent from the CI environment the name is never bound on
        the module object.  patch() and patch.object() both require the
        attribute to pre-exist.  We therefore use setattr/delattr directly
        (via _inject_requests) which works whether or not requests is installed.
        """
        with patch("core.atlas._REQUESTS_AVAILABLE", True):
            with _inject_requests(side_effect=Exception("Network error")):
                kp = self.reader.fetch_kp()
                assert kp == GeomagneticReader._DEFAULT_KP


# ─────────────────────────────────────────────────────────────────────────────
# EarthPulse Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEarthPulse:

    def _make_pulse(
        self,
        kp: float = 2.0,
        coherence: float = 0.75,
        geo_state: GeomagneticState = GeomagneticState.QUIET,
        status: AtlasStatus = AtlasStatus.MODELED,
    ) -> EarthPulse:
        return EarthPulse(
            timestamp=time.time(),
            schumann_hz=7.83,
            schumann_amplitude=0.8,
            schumann_harmonics=[7.83, 14.3, 20.8, 27.3, 33.8],
            dominant_mode=SchumannMode.FUNDAMENTAL,
            kp_index=kp,
            geomagnetic_state=geo_state,
            solar_wind_bz=2.0,
            coherence_baseline=coherence,
            viriditas_carrier_hz=31.32,
            atlas_status=status,
            source="test",
        )

    def test_coherence_friendly_quiet_high_coherence(self):
        pulse = self._make_pulse(kp=1.0, coherence=0.7, geo_state=GeomagneticState.QUIET)
        assert pulse.is_coherence_friendly is True

    def test_not_coherence_friendly_during_storm(self):
        pulse = self._make_pulse(
            kp=7.0,
            coherence=0.4,
            geo_state=GeomagneticState.MAJOR_STORM,
        )
        assert pulse.is_coherence_friendly is False

    def test_storm_warning_major(self):
        pulse = self._make_pulse(geo_state=GeomagneticState.MAJOR_STORM)
        assert pulse.storm_warning is True

    def test_storm_warning_false_quiet(self):
        pulse = self._make_pulse(geo_state=GeomagneticState.QUIET)
        assert pulse.storm_warning is False

    def test_to_dict_keys(self):
        pulse = self._make_pulse()
        d = pulse.to_dict()
        required_keys = [
            "timestamp", "schumann_hz", "schumann_amplitude",
            "schumann_harmonics", "dominant_mode", "kp_index",
            "geomagnetic_state", "solar_wind_bz", "coherence_baseline",
            "viriditas_carrier_hz", "atlas_status", "source",
            "coherence_friendly", "storm_warning",
        ]
        for key in required_keys:
            assert key in d, f"Missing key: {key}"

    def test_summary_string(self):
        pulse = self._make_pulse()
        summary = pulse.summary()
        assert "Schumann" in summary
        assert "Kp" in summary
        assert "Coherence" in summary

    def test_to_dict_numeric_precision(self):
        pulse = self._make_pulse(coherence=0.123456789)
        d = pulse.to_dict()
        assert d["coherence_baseline"] == round(0.123456789, 4)


# ─────────────────────────────────────────────────────────────────────────────
# AtlasEngine Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAtlasEngine:

    def setup_method(self):
        with patch("core.atlas._REQUESTS_AVAILABLE", False):
            self.engine = AtlasEngine()

    def test_pulse_returns_earth_pulse(self):
        pulse = self.engine.pulse()
        assert isinstance(pulse, EarthPulse)

    def test_pulse_has_valid_hz(self):
        pulse = self.engine.pulse()
        assert 6.0 <= pulse.schumann_hz <= 10.0

    def test_pulse_coherence_in_range(self):
        pulse = self.engine.pulse()
        assert 0.0 <= pulse.coherence_baseline <= 1.0

    def test_pulse_has_harmonics(self):
        pulse = self.engine.pulse()
        assert len(pulse.schumann_harmonics) == 5

    def test_offline_status_when_no_requests(self):
        pulse = self.engine.pulse()
        assert pulse.atlas_status in (AtlasStatus.MODELED, AtlasStatus.OFFLINE)

    def test_history_grows_on_refresh(self):
        initial = len(self.engine.history(n=100))
        self.engine.refresh()
        after = len(self.engine.history(n=100))
        assert after >= initial

    def test_daily_coherence_average_in_range(self):
        avg = self.engine.daily_coherence_average()
        assert 0.0 <= avg <= 1.0

    def test_to_status_keys(self):
        status = self.engine.to_status()
        assert "doctrine" in status
        assert "status" in status
        assert "current_pulse" in status
        assert "daily_coherence_avg" in status

    def test_fallback_pulse_is_safe(self):
        pulse = self.engine._fallback_pulse()
        assert isinstance(pulse, EarthPulse)
        assert pulse.atlas_status == AtlasStatus.OFFLINE
        assert 0.0 <= pulse.coherence_baseline <= 1.0

    def test_history_capped_at_288(self):
        for _ in range(300):
            self.engine._refresh()
        assert len(self.engine.history(n=1000)) <= 288

    def test_viriditas_carrier_is_positive(self):
        pulse = self.engine.pulse()
        assert pulse.viriditas_carrier_hz > 0


# ─────────────────────────────────────────────────────────────────────────────
# Singleton Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestAtlasSingleton:

    def test_get_atlas_returns_engine(self):
        atlas = get_atlas()
        assert isinstance(atlas, AtlasEngine)

    def test_get_atlas_idempotent(self):
        a1 = get_atlas()
        a2 = get_atlas()
        assert a1 is a2

    def test_singleton_pulse_consistent(self):
        atlas = get_atlas()
        p1 = atlas.pulse()
        p2 = atlas.pulse()
        assert p1 is p2


# ─────────────────────────────────────────────────────────────────────────────
# Integration: Atlas → Viriditas carrier alignment
# ─────────────────────────────────────────────────────────────────────────────

class TestAtlasViriditasIntegration:

    def test_carrier_hz_matches_viriditas_stage(self):
        from core.viriditas_magnum_opus import SCHUMANN_HARMONICS
        with patch("core.atlas._REQUESTS_AVAILABLE", False):
            engine = AtlasEngine()
        pulse = engine.pulse()
        valid_carriers = list(SCHUMANN_HARMONICS.values())
        assert pulse.viriditas_carrier_hz in valid_carriers, (
            f"Carrier {pulse.viriditas_carrier_hz} not in VMO harmonics: {valid_carriers}"
        )

    def test_coherence_friendly_when_quiet(self):
        with patch("core.atlas._REQUESTS_AVAILABLE", False):
            engine = AtlasEngine()
        pulse = engine.pulse()
        if pulse.geomagnetic_state == GeomagneticState.QUIET:
            assert pulse.coherence_baseline >= 0.3
