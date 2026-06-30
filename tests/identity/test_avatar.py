from __future__ import annotations

import pytest
from datetime import date

from core.identity.avatar.elemental import (
    GAIA_SCHUMANN_HZ,
    GAIA_WAVEFORM,
    GAIAWaveform,
    ZodiacElement,
    ZodiacSign,
    ELEMENTAL_PALETTES,
    ELEMENTAL_CHARACTERS,
    element_from_sign,
    waveform_for_element,
    zodiac_from_dob,
)
from core.identity.avatar.genesis import (
    GenesisQuestionnaire,
    GENESIS_QUESTIONS,
)


class TestSchumannResonance:
    def test_schumann_constant_is_correct(self):
        assert GAIA_SCHUMANN_HZ == 7.83

    def test_gaia_waveform_singleton_is_schumann(self):
        assert GAIA_WAVEFORM.frequency_hz == GAIA_SCHUMANN_HZ

    def test_gaia_waveform_is_frozen(self):
        with pytest.raises((AttributeError, TypeError)):
            GAIA_WAVEFORM.frequency_hz = 10.0

    def test_gaia_waveform_wrong_frequency_raises(self):
        with pytest.raises(ValueError, match="Schumann resonance"):
            GAIAWaveform(frequency_hz=10.0)

    def test_gaia_waveform_wrong_frequency_raises_any_deviation(self):
        with pytest.raises(ValueError):
            GAIAWaveform(frequency_hz=7.82)

    def test_gaia_waveform_contains_all_elements(self):
        elements = set(GAIA_WAVEFORM.harmonic_elements)
        assert ZodiacElement.FIRE  in elements
        assert ZodiacElement.EARTH in elements
        assert ZodiacElement.AIR   in elements
        assert ZodiacElement.WATER in elements

    def test_gaia_waveform_shape_is_lissajous_braid(self):
        assert GAIA_WAVEFORM.waveform_shape == "lissajous_braid"

    def test_gaia_waveform_summary_is_grounded(self):
        s = GAIA_WAVEFORM.summary()
        assert s["frequency_hz"] == 7.83
        assert "Schumann" in s["frequency_name"]
        assert "Not metaphor" in s["physical_grounding"]


class TestZodiacSystem:
    def test_fire_signs(self):
        assert element_from_sign(ZodiacSign.ARIES)       == ZodiacElement.FIRE
        assert element_from_sign(ZodiacSign.LEO)         == ZodiacElement.FIRE
        assert element_from_sign(ZodiacSign.SAGITTARIUS) == ZodiacElement.FIRE

    def test_earth_signs(self):
        assert element_from_sign(ZodiacSign.TAURUS)    == ZodiacElement.EARTH
        assert element_from_sign(ZodiacSign.VIRGO)     == ZodiacElement.EARTH
        assert element_from_sign(ZodiacSign.CAPRICORN) == ZodiacElement.EARTH

    def test_air_signs(self):
        assert element_from_sign(ZodiacSign.GEMINI)   == ZodiacElement.AIR
        assert element_from_sign(ZodiacSign.LIBRA)    == ZodiacElement.AIR
        assert element_from_sign(ZodiacSign.AQUARIUS) == ZodiacElement.AIR

    def test_water_signs(self):
        assert element_from_sign(ZodiacSign.CANCER)  == ZodiacElement.WATER
        assert element_from_sign(ZodiacSign.SCORPIO) == ZodiacElement.WATER
        assert element_from_sign(ZodiacSign.PISCES)  == ZodiacElement.WATER

    def test_dob_to_zodiac_leo(self):
        assert zodiac_from_dob(date(1990, 8, 5)) == ZodiacSign.LEO

    def test_dob_to_zodiac_pisces(self):
        assert zodiac_from_dob(date(1995, 3, 1)) == ZodiacSign.PISCES

    def test_dob_to_zodiac_capricorn_dec(self):
        assert zodiac_from_dob(date(2000, 12, 25)) == ZodiacSign.CAPRICORN

    def test_dob_to_zodiac_capricorn_jan(self):
        assert zodiac_from_dob(date(2000, 1, 10)) == ZodiacSign.CAPRICORN


class TestElementalPalettes:
    def test_all_elements_have_palettes(self):
        for element in ZodiacElement:
            assert element in ELEMENTAL_PALETTES

    def test_fire_palette_is_warm(self):
        p = ELEMENTAL_PALETTES[ZodiacElement.FIRE]
        r, g, b = p.primary
        assert r > g and r > b  # red dominant

    def test_water_palette_is_deep_blue(self):
        p = ELEMENTAL_PALETTES[ZodiacElement.WATER]
        r, g, b = p.primary
        assert b > r  # blue dominant

    def test_earth_palette_is_green(self):
        p = ELEMENTAL_PALETTES[ZodiacElement.EARTH]
        r, g, b = p.primary
        assert g > r and g > b  # green dominant


class TestWaveformCharacters:
    def test_fire_is_fastest(self):
        fire = ELEMENTAL_CHARACTERS[ZodiacElement.FIRE]
        earth = ELEMENTAL_CHARACTERS[ZodiacElement.EARTH]
        assert fire.base_frequency_hz > earth.base_frequency_hz

    def test_earth_has_lowest_variance(self):
        variances = {e: ELEMENTAL_CHARACTERS[e].amplitude_variance for e in ZodiacElement}
        assert variances[ZodiacElement.EARTH] == min(variances.values())

    def test_fire_has_sawtooth(self):
        assert ELEMENTAL_CHARACTERS[ZodiacElement.FIRE].waveform_shape == "sawtooth"

    def test_water_has_sinusoidal_deep(self):
        assert ELEMENTAL_CHARACTERS[ZodiacElement.WATER].waveform_shape == "sinusoidal_deep"


class TestElementalWaveform:
    def test_waveform_built_from_element(self):
        wf = waveform_for_element("gaian-001", ZodiacElement.FIRE, ZodiacSign.LEO)
        assert wf.element == ZodiacElement.FIRE
        assert wf.zodiac_sign == ZodiacSign.LEO
        assert wf.palette == ELEMENTAL_PALETTES[ZodiacElement.FIRE]

    def test_waveform_summary_complete(self):
        wf = waveform_for_element("gaian-001", ZodiacElement.WATER, ZodiacSign.SCORPIO)
        s = wf.summary()
        assert s["element"] == "water"
        assert s["zodiac_sign"] == "scorpio"
        assert "frequency_hz" in s["waveform"]


class TestGenesisQuestionnaire:
    def _full_answers(self) -> dict:
        return {
            "dob": "1990-08-05",
            "birth_time": "dawn",
            "birth_place": "Cape Town, South Africa",
            "environment": "ocean",
            "sound": "rain",
            "time_of_day": "dusk",
            "thinking_style": "images and visions",
            "dream_colour": "deep teal",
            "soul_word": "home",
        }

    def test_questionnaire_requires_dob(self):
        q = GenesisQuestionnaire("gaian-001")
        assert any(qi.question_id == "dob" for qi in q.remaining_questions())

    def test_answering_returns_followup(self):
        q = GenesisQuestionnaire("gaian-001")
        followup = q.answer("dob", "1990-08-05")
        assert followup is not None
        assert len(followup) > 0

    def test_complete_ceremony(self):
        q = GenesisQuestionnaire("gaian-001")
        answers = self._full_answers()
        required_ids = [qi.question_id for qi in GENESIS_QUESTIONS if qi.required]
        for qid in required_ids:
            q.answer(qid, answers[qid])
        assert q.is_ready_to_complete()
        record = q.complete()
        assert record.completed
        assert record.date_of_birth == "1990-08-05"
        assert record.soul_word == "home"
        assert record.environment_resonance == "ocean"

    def test_record_is_immutable_after_completion(self):
        q = GenesisQuestionnaire("gaian-001")
        for qi in GENESIS_QUESTIONS:
            if qi.required:
                q.answer(qi.question_id, self._full_answers().get(qi.question_id, "test"))
        record = q.complete()
        with pytest.raises(ValueError, match="immutable"):
            record.record_response("dob", "2000-01-01")

    def test_incomplete_ceremony_cannot_complete(self):
        q = GenesisQuestionnaire("gaian-001")
        with pytest.raises(ValueError, match="unanswered"):
            q.complete()

    def test_dob_feeds_zodiac_correctly(self):
        """DoB of Aug 5 → Leo → Fire."""
        from core.identity.avatar.elemental import zodiac_from_dob, element_from_sign
        from datetime import date
        dob = date.fromisoformat("1990-08-05")
        sign = zodiac_from_dob(dob)
        element = element_from_sign(sign)
        assert sign == ZodiacSign.LEO
        assert element == ZodiacElement.FIRE
