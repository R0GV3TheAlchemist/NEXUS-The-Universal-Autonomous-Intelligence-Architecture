# Copyright (c) 2026 R0GV3 The Alchemist — GAIA Project
import pytest
from core.spectral.green.transparency import detect_viriditas_state, emit_sentinel_alert, classify_urgency, get_ui_state, is_emerald_completion_signal
from core.spectral.green.constants import GREEN_HEX, ALCHEMICAL_PHASE


class TestDetectViriditasState:
    def test_phase_match(self): assert detect_viriditas_state({"phase": ALCHEMICAL_PHASE}) is True
    def test_hex_match(self): assert detect_viriditas_state({"hex": GREEN_HEX["VIRIDITAS"]}) is True
    def test_wavelength_in_range(self): assert detect_viriditas_state({"wavelength": 530}) is True
    def test_out_of_range(self): assert detect_viriditas_state({"wavelength": 700}) is False
    def test_non_dict(self): assert detect_viriditas_state(None) is False


class TestEmitSentinelAlert:
    def test_interrupt_always_false(self):
        for lvl in (1, 2, 3):
            assert emit_sentinel_alert(lvl)["interrupt_flag"] is False


class TestClassifyUrgency:
    def test_low(self): assert classify_urgency(0.1) == "low"
    def test_high(self): assert classify_urgency(0.9) == "high"


class TestIsEmeraldCompletionSignal:
    def test_emerald_hex(self): assert is_emerald_completion_signal({"hex": GREEN_HEX["EMERALD"]}) is True
    def test_no_signal(self): assert is_emerald_completion_signal({"hex": "#000"}) is False
