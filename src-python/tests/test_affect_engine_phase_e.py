# Copyright (c) 2026 Kyle Alexander Steen (R0GV3 The Alchemist). All Rights Reserved.
# NEXUS Affect Engine — Phase E operational test suite
# Tests: PAD model, label classifier, signal parsers (text/biometric/schumann),
#        EMA blending, arc trend, multi-modal fusion, Ledger integration.

from __future__ import annotations

import threading
from unittest.mock import MagicMock

import pytest

from affect_engine.engine import AffectEngine
from affect_engine.pad import AffectState, classify_pad, clamp
from affect_engine.signal_parsers import (
    BiometricParser,
    SchumannSyncParser,
    TextSentimentParser,
)


# ---------------------------------------------------------------------------
# PAD model unit tests
# ---------------------------------------------------------------------------

class TestAffectState:
    def test_default_is_neutral(self):
        s = AffectState()
        assert s.pleasure == 0.0
        assert s.arousal == 0.5
        assert s.dominance == 0.5

    def test_clamps_pleasure(self):
        s = AffectState(pleasure=5.0)
        assert s.pleasure == 1.0
        s2 = AffectState(pleasure=-5.0)
        assert s2.pleasure == -1.0

    def test_clamps_arousal(self):
        s = AffectState(arousal=2.0)
        assert s.arousal == 1.0

    def test_to_dict_keys(self):
        d = AffectState().to_dict()
        for k in ("pleasure", "arousal", "dominance", "label", "timestamp", "confidence"):
            assert k in d

    def test_blend_moves_toward_other(self):
        base  = AffectState(pleasure=0.0, arousal=0.5, dominance=0.5)
        other = AffectState(pleasure=1.0, arousal=0.5, dominance=0.5)
        blended = base.blend(other, alpha=0.5)
        assert 0.0 < blended.pleasure < 1.0

    def test_blend_ema_weight(self):
        base  = AffectState(pleasure=0.0, arousal=0.5, dominance=0.5, label="neutral")
        other = AffectState(pleasure=1.0, arousal=0.5, dominance=0.5, label="elated")
        blended = base.blend(other, alpha=0.35)
        assert round(blended.pleasure, 4) == round(0.0 + 0.35 * (1.0 - 0.0), 4)


class TestClassifyPAD:
    def test_calm_region(self):
        assert classify_pad(0.5, 0.2, 0.6) == "calm"

    def test_anxious_region(self):
        assert classify_pad(-0.3, 0.8, 0.2) in ("anxious", "tense", "distressed")

    def test_happy_region(self):
        assert classify_pad(0.7, 0.5, 0.7) in ("happy", "excited", "elated")

    def test_neutral_fallback(self):
        label = classify_pad(0.0, 0.45, 0.5)
        assert isinstance(label, str)
        assert len(label) > 0

    def test_returns_string_always(self):
        import random
        for _ in range(20):
            p = random.uniform(-1, 1)
            a = random.uniform(0, 1)
            d = random.uniform(0, 1)
            assert isinstance(classify_pad(p, a, d), str)


# ---------------------------------------------------------------------------
# Signal parser tests
# ---------------------------------------------------------------------------

class TestTextSentimentParser:
    def setup_method(self):
        self.parser = TextSentimentParser()

    def test_positive_text_raises_pleasure(self):
        delta = self.parser.parse("I feel amazing and happy today")
        assert delta.pleasure > 0

    def test_negative_text_lowers_pleasure(self):
        delta = self.parser.parse("I feel terrible and sad")
        assert delta.pleasure < 0

    def test_empty_text_neutral(self):
        delta = self.parser.parse("")
        assert delta.pleasure == 0.0
        assert delta.arousal == 0.0

    def test_high_arousal_words(self):
        delta = self.parser.parse("urgent emergency now immediately")
        assert delta.arousal > 0

    def test_low_arousal_words(self):
        delta = self.parser.parse("calm peaceful quiet relaxed serene")
        assert delta.arousal < 0

    def test_source_is_text(self):
        assert self.parser.parse("hello").source == "text"


class TestBiometricParser:
    def setup_method(self):
        self.parser = BiometricParser()

    def test_elevated_hr_increases_arousal(self):
        delta = self.parser.parse(heart_rate=100.0)
        assert delta.arousal > 0

    def test_high_hrv_increases_pleasure(self):
        delta = self.parser.parse(hrv=80.0)
        assert delta.pleasure > 0

    def test_low_hrv_decreases_pleasure(self):
        delta = self.parser.parse(hrv=20.0)
        assert delta.pleasure < 0

    def test_no_signal_zero_deltas(self):
        delta = self.parser.parse()
        assert delta.pleasure == 0.0
        assert delta.arousal == 0.0

    def test_source_is_biometric(self):
        assert self.parser.parse(heart_rate=70.0).source == "biometric"

    def test_skin_conductance_raises_arousal(self):
        delta = self.parser.parse(skin_conductance=20.0)
        assert delta.arousal > 0


class TestSchumannSyncParser:
    def setup_method(self):
        self.parser = SchumannSyncParser()

    def test_high_alignment_positive_pleasure(self):
        delta = self.parser.parse(alignment_score=1.0, coherence=1.0)
        assert delta.pleasure > 0

    def test_high_alignment_lowers_arousal(self):
        delta = self.parser.parse(alignment_score=1.0, coherence=1.0)
        assert delta.arousal < 0

    def test_zero_alignment_zero_delta(self):
        delta = self.parser.parse(alignment_score=0.0, coherence=0.0)
        assert delta.pleasure == 0.0
        assert delta.arousal == 0.0

    def test_source_is_schumann(self):
        assert self.parser.parse(1.0, 1.0).source == "schumann"


# ---------------------------------------------------------------------------
# AffectEngine integration tests
# ---------------------------------------------------------------------------

class TestAffectEngine:
    def test_default_state_neutral(self):
        e = AffectEngine()
        assert e.state.pleasure == 0.0

    def test_ingest_text_updates_state(self):
        e = AffectEngine()
        state = e.ingest({"text": "I feel excited and amazing"})
        assert state.pleasure > 0.0
        assert isinstance(state.label, str)

    def test_ingest_biometric(self):
        e = AffectEngine()
        state = e.ingest({"heart_rate": 55.0, "hrv": 75.0})
        assert isinstance(state, AffectState)

    def test_ingest_schumann(self):
        e = AffectEngine()
        state = e.ingest({"schumann_alignment": 0.9, "schumann_coherence": 0.85})
        assert isinstance(state, AffectState)

    def test_ingest_direct_pad(self):
        e = AffectEngine()
        state = e.ingest({"pleasure": 0.8, "arousal": 0.3, "dominance": 0.7})
        assert state.pleasure > 0

    def test_multimodal_fusion(self):
        e = AffectEngine()
        state = e.ingest({
            "text": "feeling calm and focused",
            "heart_rate": 65.0,
            "hrv": 58.0,
            "schumann_alignment": 0.85,
            "schumann_coherence": 0.9,
        })
        assert isinstance(state.label, str)
        assert -1.0 <= state.pleasure <= 1.0
        assert 0.0 <= state.arousal <= 1.0

    def test_history_accumulates(self):
        e = AffectEngine()
        for _ in range(5):
            e.ingest({"text": "good progress"})
        assert len(e.history) == 5

    def test_arc_trend_empty(self):
        e = AffectEngine()
        trend = e.arc_trend()
        assert trend["window"] == 0
        assert trend["trajectory"] == "stable"

    def test_arc_trend_rising(self):
        e = AffectEngine()
        for i in range(10):
            e.ingest({"pleasure": i * 0.08, "arousal": 0.5, "dominance": 0.5})
        trend = e.arc_trend(window=10)
        assert trend["pleasure_delta"] > 0

    def test_arc_trend_dominant_label(self):
        e = AffectEngine()
        for _ in range(10):
            e.ingest({"text": "great amazing happy wonderful"})
        trend = e.arc_trend(window=10)
        assert isinstance(trend["dominant_label"], str)

    def test_reset_clears_state(self):
        e = AffectEngine()
        e.ingest({"pleasure": 0.9, "arousal": 0.8, "dominance": 0.8})
        e.reset()
        assert e.state.pleasure == 0.0
        assert len(e.history) == 0

    def test_empty_signal_no_change(self):
        e = AffectEngine()
        state = e.ingest({})
        assert state.pleasure == 0.0

    def test_ledger_called_on_ingest(self):
        mock_ledger = MagicMock()
        e = AffectEngine(ledger=mock_ledger, session_id="s-ae-001")
        e.ingest({"text": "hello"})
        mock_ledger.append.assert_called_once()

    def test_no_ledger_runs_cleanly(self):
        e = AffectEngine(ledger=None)
        state = e.ingest({"text": "fine"})
        assert state is not None

    def test_concurrent_ingest_thread_safe(self):
        e = AffectEngine()
        errors: list[Exception] = []

        def worker(i: int) -> None:
            try:
                e.ingest({"text": f"signal {i}", "heart_rate": 65.0 + i})
            except Exception as ex:
                errors.append(ex)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []
