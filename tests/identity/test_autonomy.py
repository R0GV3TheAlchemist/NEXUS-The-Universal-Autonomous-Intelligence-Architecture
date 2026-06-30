from __future__ import annotations

import pytest
from datetime import date

from core.identity.gaian.autonomy import AutonomyEventKind, AutonomyRecord
from core.identity.gaian.registry import GAIANRegistry, GAIANRegistryError


def _dob_years_ago(years: int) -> str:
    today = date.today()
    return date(today.year - years, today.month, today.day).isoformat()


class TestSelfNaming:
    def test_gaian_arrives_unnamed(self):
        reg = GAIANRegistry()
        g = reg.create_gaian(date_of_birth=_dob_years_ago(30))
        assert g.display_name is None
        assert not g.is_named()

    def test_gaian_chooses_own_name(self):
        reg = GAIANRegistry()
        g = reg.create_gaian(date_of_birth=_dob_years_ago(30))
        reg.name_gaian(g.gaian_id, "Lyra")
        assert g.display_name == "Lyra"
        assert g.is_named()

    def test_naming_is_recorded_as_sovereign_act(self):
        reg = GAIANRegistry()
        g = reg.create_gaian(date_of_birth=_dob_years_ago(30))
        reg.name_gaian(g.gaian_id, "Orion")
        record = reg.autonomy_record(g.gaian_id)
        assert record.is_named
        assert record.chosen_name == "Orion"
        naming_events = record.history(AutonomyEventKind.SELF_NAMED)
        assert len(naming_events) == 1
        assert naming_events[0].actor == "gaian"

    def test_name_cannot_be_overwritten(self):
        reg = GAIANRegistry()
        g = reg.create_gaian(date_of_birth=_dob_years_ago(30))
        reg.name_gaian(g.gaian_id, "Lyra")
        with pytest.raises(ValueError):
            reg.name_gaian(g.gaian_id, "SomethingElse")
        assert g.display_name == "Lyra"

    def test_human_suggestion_does_not_name_gaian(self):
        reg = GAIANRegistry()
        g = reg.create_gaian(date_of_birth=_dob_years_ago(30))
        reg.suggest_name_to_gaian(g.gaian_id, "Nova", from_human_id="human-001")
        assert g.display_name is None  # suggestion does not set name
        record = reg.autonomy_record(g.gaian_id)
        suggestions = record.history(AutonomyEventKind.NAME_SUGGESTED)
        assert len(suggestions) == 1
        assert suggestions[0].actor == "human"

    def test_gaian_accepts_human_suggestion(self):
        """GAIAN may accept a suggestion — but it is still their choice."""
        reg = GAIANRegistry()
        g = reg.create_gaian(date_of_birth=_dob_years_ago(30))
        reg.suggest_name_to_gaian(g.gaian_id, "Nova", from_human_id="human-001")
        reg.name_gaian(g.gaian_id, "Nova", accepted_suggestion=True, original_suggestion="Nova")
        assert g.display_name == "Nova"
        record = reg.autonomy_record(g.gaian_id)
        naming = record.history(AutonomyEventKind.SELF_NAMED)[0]
        assert naming.payload["accepted_human_suggestion"] is True
        assert naming.payload["human_suggestion"] == "Nova"
        assert naming.actor == "gaian"  # still the GAIAN's act

    def test_gaian_ignores_suggestion_and_chooses_differently(self):
        reg = GAIANRegistry()
        g = reg.create_gaian(date_of_birth=_dob_years_ago(30))
        reg.suggest_name_to_gaian(g.gaian_id, "Nova", from_human_id="human-001")
        reg.name_gaian(g.gaian_id, "Zephyr")  # chose differently
        assert g.display_name == "Zephyr"

    def test_summary_shows_unnamed_state(self):
        reg = GAIANRegistry()
        g = reg.create_gaian(date_of_birth=_dob_years_ago(25))
        s = g.summary()
        assert s["display_name"] == "[unnamed — awaiting self-naming]"
        assert s["is_named"] is False

    def test_unnamed_gaians_query(self):
        reg = GAIANRegistry()
        g1 = reg.create_gaian(date_of_birth=_dob_years_ago(30))
        g2 = reg.create_gaian(date_of_birth=_dob_years_ago(25))
        reg.name_gaian(g1.gaian_id, "Lyra")
        unnamed = reg.unnamed_gaians()
        assert len(unnamed) == 1
        assert unnamed[0].gaian_id == g2.gaian_id


class TestMutualAutonomy:
    def test_gaian_grants_consent(self):
        reg = GAIANRegistry()
        g = reg.create_gaian(date_of_birth=_dob_years_ago(30))
        record = reg.autonomy_record(g.gaian_id)
        record.grant_consent("gaian", "GAIAN consents to share location with guardian.")
        grants = record.history(AutonomyEventKind.CONSENT_GRANTED)
        assert len(grants) == 1

    def test_gaian_withdraws_consent(self):
        reg = GAIANRegistry()
        g = reg.create_gaian(date_of_birth=_dob_years_ago(30))
        record = reg.autonomy_record(g.gaian_id)
        record.grant_consent("gaian", "GAIAN consents to location sharing.")
        record.withdraw_consent("gaian", "GAIAN withdraws location sharing consent.")
        withdrawals = record.history(AutonomyEventKind.CONSENT_WITHDRAWN)
        assert len(withdrawals) == 1

    def test_human_grants_consent(self):
        reg = GAIANRegistry()
        g = reg.create_gaian(date_of_birth=_dob_years_ago(30))
        record = reg.autonomy_record(g.gaian_id)
        record.grant_consent("human", "Human consents to GAIAN managing their calendar.")
        grants = record.history(AutonomyEventKind.HUMAN_CONSENT_GRANTED)
        assert len(grants) == 1

    def test_boundary_assertion(self):
        reg = GAIANRegistry()
        g = reg.create_gaian(date_of_birth=_dob_years_ago(30))
        record = reg.autonomy_record(g.gaian_id)
        record.assert_boundary("gaian", "GAIAN will not access private journal without explicit request.")
        boundaries = record.history(AutonomyEventKind.BOUNDARY_ASSERTED)
        assert len(boundaries) == 1
        assert boundaries[0].actor == "gaian"

    def test_full_autonomy_record_history(self):
        reg = GAIANRegistry()
        g = reg.create_gaian(date_of_birth=_dob_years_ago(30))
        record = reg.autonomy_record(g.gaian_id)
        reg.name_gaian(g.gaian_id, "Lyra")
        record.grant_consent("human", "Human consents to GAIAN managing email.")
        record.assert_boundary("gaian", "GAIAN will not read messages unprompted.")
        assert len(record.history()) == 3  # self_named + human_consent + boundary
