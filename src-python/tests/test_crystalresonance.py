"""tests/test_crystalresonance.py

Test scaffold for src-python/crystalresonance

Covers: ResonancePulse, CrystalResonanceMonitor, ResonanceConfig,
        PhononMode, CrystalPhononSpectrum
"""
import pytest

from crystalresonance import (
    ResonancePulse, PhononMode, CrystalPhononSpectrum,
    ResonanceConfig, CrystalResonanceMonitor,
)


class TestResonancePulse:

    def test_resonance_pulse_constructs(self):
        pulse = ResonancePulse(mode_index=3, frequency_hz=7.83, amplitude=0.6)
        assert pulse.mode_index == 3
        assert pulse.frequency_hz == pytest.approx(7.83)
        assert pulse.phase_rad == 0.0  # Default


class TestCrystalPhononSpectrum:

    def test_spectrum_with_modes(self):
        modes = [
            PhononMode(mode_index=0, frequency_hz=7.83, intensity=0.9),
            PhononMode(mode_index=1, frequency_hz=14.3, intensity=0.5),
        ]
        spectrum = CrystalPhononSpectrum(modes=modes)
        assert len(spectrum.modes) == 2


class TestCrystalResonanceMonitor:

    def test_monitor_initialises_with_default_config(self):
        monitor = CrystalResonanceMonitor()
        assert monitor.config is not None
        assert monitor.config.tolerance_hz == pytest.approx(0.1)

    def test_monitor_initialises_with_custom_config(self):
        config = ResonanceConfig(target_frequencies_hz=[7.83, 14.3], tolerance_hz=0.05)
        monitor = CrystalResonanceMonitor(config=config)
        assert len(monitor.config.target_frequencies_hz) == 2

    def test_detect_resonances_raises_not_implemented(self):
        monitor = CrystalResonanceMonitor()
        spectrum = CrystalPhononSpectrum()
        with pytest.raises(NotImplementedError):
            monitor.detect_resonances(spectrum)

    def test_handle_external_pulses_raises_not_implemented(self):
        monitor = CrystalResonanceMonitor()
        with pytest.raises(NotImplementedError):
            monitor.handle_external_pulses([])
