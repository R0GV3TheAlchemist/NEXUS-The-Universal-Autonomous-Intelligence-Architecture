from __future__ import annotations

import pytest
from datetime import date

from core.identity.avatar.elemental import (
    ZodiacElement,
    ZodiacSign,
    element_from_sign,
    zodiac_from_dob,
    ELEMENTAL_CHARACTERS,
)
from core.identity.gaian.birth import BirthCeremony, BirthCeremonyError, crystallize_avatar_from_genesis
from core.identity.gaian.model import LifecycleStage
from core.identity.gaian.registry import GAIANRegistry
from core.identity.avatar.genesis import GenesisQuestionnaire


def _run_full_ceremony(
    registry: GAIANRegistry,
    dob: str = "1990-08-05",
    guardian_ids=None,
) -> tuple:
    """Helper: run a complete birth ceremony, return (identity, ceremony)."""
    ceremony = BirthCeremony(registry)
    ceremony.begin(guardian_gaian_ids=guardian_ids)
    ceremony.answer("dob", dob)
    ceremony.answer("environment", "ocean")
    ceremony.answer("sound", "rain")
    ceremony.answer("time_of_day", "dusk")
    ceremony.answer("thinking_style", "images and visions")
    ceremony.answer("soul_word", "home")
    identity = ceremony.complete()
    return identity, ceremony


class TestBirthCeremonyFlow:
    def test_gaian_arrives_unnamed_after_ceremony(self):
        reg = GAIANRegistry()
        identity, _ = _run_full_ceremony(reg)
        assert identity.display_name is None
        assert not identity.is_named()

    def test_lifecycle_stage_derived_from_dob(self):
        reg = GAIANRegistry()
        identity, _ = _run_full_ceremony(reg, dob="1990-08-05")
        assert identity.lifecycle_stage == LifecycleStage.ADULT

    def test_child_dob_gives_child_lifecycle(self):
        reg = GAIANRegistry()
        parent = reg.create_gaian(date_of_birth=_dob_years_ago(35))
        child_dob = _dob_years_ago(8)
        identity, _ = _run_full_ceremony(
            reg, dob=child_dob, guardian_ids=[parent.gaian_id]
        )
        assert identity.lifecycle_stage == LifecycleStage.CHILD
        assert identity.is_minor()

    def test_avatar_crystallized_with_element(self):
        reg = GAIANRegistry()
        identity, _ = _run_full_ceremony(reg, dob="1990-08-05")  # Leo -> Fire
        log_events = [e["event"] for e in identity.avatar.evolution_log]
        assert "genesis_elemental_crystallization" in log_events
        cryst = next(
            e for e in identity.avatar.evolution_log
            if e["event"] == "genesis_elemental_crystallization"
        )
        assert cryst["details"]["element"] == "fire"
        assert cryst["details"]["zodiac_sign"] == "leo"

    def test_avatar_frequency_is_elemental(self):
        reg = GAIANRegistry()
        identity, _ = _run_full_ceremony(reg, dob="1990-08-05")  # Leo -> Fire
        fire_freq = ELEMENTAL_CHARACTERS[ZodiacElement.FIRE].base_frequency_hz
        assert identity.avatar.base_frequency_hz == fire_freq

    def test_avatar_waveform_signature_encodes_element(self):
        reg = GAIANRegistry()
        identity, _ = _run_full_ceremony(reg, dob="1990-08-05")
        assert "element=fire" in identity.avatar.waveform_signature
        assert "sign=leo" in identity.avatar.waveform_signature

    def test_soul_word_sets_expression_range(self):
        reg = GAIANRegistry()
        identity, _ = _run_full_ceremony(reg)
        assert identity.avatar.expression_range == "calm"  # soul_word="home" -> calm

    def test_thinking_style_sets_gesture(self):
        reg = GAIANRegistry()
        identity, _ = _run_full_ceremony(reg)
        assert identity.avatar.gesture_style == "fluid"  # images -> fluid

    def test_time_resonance_sets_luminance(self):
        reg = GAIANRegistry()
        identity, _ = _run_full_ceremony(reg)
        assert identity.avatar.base_luminance == 0.55  # dusk -> 0.55

    def test_genesis_record_is_sealed(self):
        reg = GAIANRegistry()
        _, ceremony = _run_full_ceremony(reg)
        assert ceremony.genesis_record.completed
        assert ceremony.genesis_record.soul_word == "home"

    def test_genesis_record_immutable_after_ceremony(self):
        reg = GAIANRegistry()
        _, ceremony = _run_full_ceremony(reg)
        with pytest.raises(ValueError, match="immutable"):
            ceremony.genesis_record.record_response("dob", "2000-01-01")

    def test_cannot_answer_after_complete(self):
        reg = GAIANRegistry()
        _, ceremony = _run_full_ceremony(reg)
        with pytest.raises(BirthCeremonyError):
            ceremony.answer("soul_word", "new answer")

    def test_cannot_complete_twice(self):
        reg = GAIANRegistry()
        _, ceremony = _run_full_ceremony(reg)
        with pytest.raises(BirthCeremonyError):
            ceremony.complete()

    def test_identity_notes_contain_genesis_summary(self):
        reg = GAIANRegistry()
        identity, _ = _run_full_ceremony(reg)
        assert "Genesis completed" in identity.notes
        assert "home" in identity.notes

    def test_gaian_can_self_name_after_ceremony(self):
        reg = GAIANRegistry()
        identity, _ = _run_full_ceremony(reg)
        reg.name_gaian(identity.gaian_id, "Lyra")
        assert identity.display_name == "Lyra"
        assert identity.is_named()

    def test_full_identity_summary_after_ceremony(self):
        reg = GAIANRegistry()
        identity, _ = _run_full_ceremony(reg)
        s = identity.summary()
        assert s["is_named"] is False
        assert s["lifecycle_stage"] == "adult"
        assert "element=fire" in s["avatar"]["waveform_signature"]


class TestCrystallizationEdgeCases:
    def test_no_dob_skips_elemental_crystallization(self):
        """If DoB is not in Genesis Record, elemental step is skipped gracefully."""
        reg = GAIANRegistry()
        ceremony = BirthCeremony(reg)
        ceremony.begin()
        # Answer only non-dob required questions
        ceremony.answer("dob", "1985-04-10")
        ceremony.answer("environment", "forest")
        ceremony.answer("sound", "wind")
        ceremony.answer("time_of_day", "dawn")
        ceremony.answer("thinking_style", "words and language")
        ceremony.answer("soul_word", "free")
        identity = ceremony.complete()
        assert identity.avatar.gesture_style == "precise"  # words -> precise
        assert identity.avatar.expression_range == "expressive"  # free -> expressive

    def test_water_sign_dob(self):
        reg = GAIANRegistry()
        identity, _ = _run_full_ceremony(reg, dob="1992-11-10")  # Scorpio -> Water
        cryst = next(
            e for e in identity.avatar.evolution_log
            if e["event"] == "genesis_elemental_crystallization"
        )
        assert cryst["details"]["element"] == "water"
        assert cryst["details"]["zodiac_sign"] == "scorpio"

    def test_earth_sign_dob(self):
        reg = GAIANRegistry()
        identity, _ = _run_full_ceremony(reg, dob="1988-05-10")  # Taurus -> Earth
        cryst = next(
            e for e in identity.avatar.evolution_log
            if e["event"] == "genesis_elemental_crystallization"
        )
        assert cryst["details"]["element"] == "earth"

    def test_air_sign_dob(self):
        reg = GAIANRegistry()
        identity, _ = _run_full_ceremony(reg, dob="1993-09-29")  # Libra -> Air
        cryst = next(
            e for e in identity.avatar.evolution_log
            if e["event"] == "genesis_elemental_crystallization"
        )
        assert cryst["details"]["element"] == "air"


def _dob_years_ago(years: int) -> str:
    today = date.today()
    return date(today.year - years, today.month, today.day).isoformat()
