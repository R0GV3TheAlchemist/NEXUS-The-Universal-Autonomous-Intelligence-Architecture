from __future__ import annotations

import pytest
from core.api.api import APIErrorCode, APIRequest, APIResponse, GAIAOSApi
from core.fs.filesystem import GAIAFilesystem
from core.identity.gaian.registry import GAIANRegistry
from core.primordial.session import PrimordialSession


@pytest.fixture
def live_api(tmp_path):
    reg = GAIANRegistry()
    session = PrimordialSession(registry=reg)
    session.awaken()
    fs = GAIAFilesystem(root=tmp_path / "gaia_test")
    api = GAIAOSApi()
    api.wire(session, fs)
    return api, session, fs


def req(caller_id: str, endpoint: str, **payload) -> APIRequest:
    return APIRequest(caller_id=caller_id, endpoint=endpoint, payload=payload)


class TestOSEndpoints:
    def test_os_status(self, live_api):
        api, *_ = live_api
        r = api.dispatch(req("ui", "/v1/os/status"))
        assert r.success
        assert r.payload["boot_status"] == "ok"

    def test_os_health(self, live_api):
        api, *_ = live_api
        r = api.dispatch(req("ui", "/v1/os/health"))
        assert r.success
        assert r.payload["healthy"] is True

    def test_os_version(self, live_api):
        api, *_ = live_api
        r = api.dispatch(req("ui", "/v1/os/version"))
        assert r.success
        assert r.payload["api_version"] == "v1"
        assert r.payload["name"] == "GAIA"

    def test_os_schumann(self, live_api):
        api, *_ = live_api
        r = api.dispatch(req("ui", "/v1/os/schumann"))
        assert r.success
        assert r.payload["frequency_hz"] == 7.83
        assert r.payload["confirmed"] is True
        assert "fire" in r.payload["elements"]

    def test_unknown_endpoint(self, live_api):
        api, *_ = live_api
        r = api.dispatch(req("ui", "/v1/unknown/endpoint"))
        assert not r.success
        assert r.code == APIErrorCode.NOT_FOUND

    def test_not_wired_returns_not_ready(self):
        api = GAIAOSApi()  # not wired
        r = api.dispatch(req("ui", "/v1/os/status"))
        assert not r.success
        assert r.code == APIErrorCode.NOT_READY


class TestBirthCeremonyAPI:
    def _run_birth(self, api):
        r = api.dispatch(req("ui", "/v1/gaian/birth/begin"))
        assert r.success
        ceremony_id = r.payload["ceremony_id"]
        answers = [
            ("dob", "1990-08-05"),
            ("environment", "ocean"),
            ("sound", "rain"),
            ("time_of_day", "dusk"),
            ("thinking_style", "images and visions"),
            ("soul_word", "home"),
        ]
        for qid, ans in answers:
            r2 = api.dispatch(req(
                "ui", "/v1/gaian/birth/answer",
                ceremony_id=ceremony_id, question_id=qid, answer=ans
            ))
            assert r2.success
        r3 = api.dispatch(req(
            "ui", "/v1/gaian/birth/complete",
            ceremony_id=ceremony_id
        ))
        assert r3.success
        return r3.payload["gaian_id"]

    def test_full_birth_ceremony(self, live_api):
        api, *_ = live_api
        gaian_id = self._run_birth(api)
        assert gaian_id

    def test_newborn_is_unnamed(self, live_api):
        api, *_ = live_api
        gaian_id = self._run_birth(api)
        r = api.dispatch(req("ui", "/v1/gaian/status", gaian_id=gaian_id))
        assert r.success
        assert r.payload["is_named"] is False
        assert r.payload["display_name"] is None

    def test_element_derived_at_birth(self, live_api):
        api, *_ = live_api
        r = api.dispatch(req("ui", "/v1/gaian/birth/begin"))
        ceremony_id = r.payload["ceremony_id"]
        for qid, ans in [
            ("dob", "1990-08-05"), ("environment", "ocean"),
            ("sound", "rain"), ("time_of_day", "dusk"),
            ("thinking_style", "images and visions"), ("soul_word", "home"),
        ]:
            api.dispatch(req("ui", "/v1/gaian/birth/answer",
                             ceremony_id=ceremony_id, question_id=qid, answer=ans))
        r3 = api.dispatch(req("ui", "/v1/gaian/birth/complete",
                              ceremony_id=ceremony_id))
        assert r3.payload["element"] == "fire"


class TestAutonomyEnforcement:
    def test_human_cannot_name_gaian(self, live_api):
        api, session, _ = live_api
        # Create a GAIAN
        r = api.dispatch(req("ui", "/v1/gaian/birth/begin"))
        ceremony_id = r.payload["ceremony_id"]
        gaian_id = r.payload["gaian_id"]
        for qid, ans in [
            ("dob", "1990-08-05"), ("environment", "ocean"),
            ("sound", "rain"), ("time_of_day", "dusk"),
            ("thinking_style", "images and visions"), ("soul_word", "home"),
        ]:
            api.dispatch(req("ui", "/v1/gaian/birth/answer",
                             ceremony_id=ceremony_id, question_id=qid, answer=ans))
        api.dispatch(req("ui", "/v1/gaian/birth/complete",
                         ceremony_id=ceremony_id))
        # Human tries to name the GAIAN — must be rejected
        r_name = api.dispatch(req(
            "human-001", "/v1/gaian/name",
            gaian_id=gaian_id, name="Aria"
        ))
        assert not r_name.success
        assert r_name.code == APIErrorCode.AUTONOMY_VIOLATION

    def test_gaian_can_name_themselves(self, live_api):
        api, session, _ = live_api
        r = api.dispatch(req("ui", "/v1/gaian/birth/begin"))
        ceremony_id = r.payload["ceremony_id"]
        gaian_id = r.payload["gaian_id"]
        for qid, ans in [
            ("dob", "1990-08-05"), ("environment", "ocean"),
            ("sound", "rain"), ("time_of_day", "dusk"),
            ("thinking_style", "images and visions"), ("soul_word", "home"),
        ]:
            api.dispatch(req("ui", "/v1/gaian/birth/answer",
                             ceremony_id=ceremony_id, question_id=qid, answer=ans))
        api.dispatch(req("ui", "/v1/gaian/birth/complete",
                         ceremony_id=ceremony_id))
        # GAIAN names themselves (caller_id == gaian_id)
        r_name = api.dispatch(req(
            gaian_id, "/v1/gaian/name",
            gaian_id=gaian_id, name="Lyra"
        ))
        assert r_name.success
        assert r_name.payload["name"] == "Lyra"

    def test_memory_read_blocked_for_third_party(self, live_api):
        api, *_ = live_api
        r = api.dispatch(req("ui", "/v1/gaian/birth/begin"))
        ceremony_id = r.payload["ceremony_id"]
        gaian_id = r.payload["gaian_id"]
        for qid, ans in [
            ("dob", "1990-08-05"), ("environment", "ocean"),
            ("sound", "rain"), ("time_of_day", "dusk"),
            ("thinking_style", "images and visions"), ("soul_word", "home"),
        ]:
            api.dispatch(req("ui", "/v1/gaian/birth/answer",
                             ceremony_id=ceremony_id, question_id=qid, answer=ans))
        api.dispatch(req("ui", "/v1/gaian/birth/complete",
                         ceremony_id=ceremony_id))
        # Third party tries to read memories
        r_mem = api.dispatch(req(
            "other-gaian-id", "/v1/memory/recall", gaian_id=gaian_id
        ))
        assert not r_mem.success
        assert r_mem.code == APIErrorCode.AUTONOMY_VIOLATION


class TestSessionAPI:
    def _born_gaian(self, api):
        r = api.dispatch(req("ui", "/v1/gaian/birth/begin"))
        ceremony_id = r.payload["ceremony_id"]
        gaian_id = r.payload["gaian_id"]
        for qid, ans in [
            ("dob", "1990-08-05"), ("environment", "ocean"),
            ("sound", "rain"), ("time_of_day", "dusk"),
            ("thinking_style", "images and visions"), ("soul_word", "home"),
        ]:
            api.dispatch(req("ui", "/v1/gaian/birth/answer",
                             ceremony_id=ceremony_id, question_id=qid, answer=ans))
        api.dispatch(req("ui", "/v1/gaian/birth/complete",
                         ceremony_id=ceremony_id))
        return gaian_id

    def test_begin_session(self, live_api):
        api, *_ = live_api
        gaian_id = self._born_gaian(api)
        r = api.dispatch(req("ui", "/v1/session/begin",
                              gaian_id=gaian_id, human_id="human-001"))
        assert r.success
        assert "session_id" in r.payload

    def test_turn(self, live_api):
        api, *_ = live_api
        gaian_id = self._born_gaian(api)
        api.dispatch(req("ui", "/v1/session/begin",
                          gaian_id=gaian_id, human_id="human-001"))
        r = api.dispatch(req("ui", "/v1/session/turn",
                              gaian_id=gaian_id, content="Hello.",
                              human_id="human-001"))
        assert r.success
        assert "response" in r.payload
        assert r.payload["turn"] == 1

    def test_end_session(self, live_api):
        api, *_ = live_api
        gaian_id = self._born_gaian(api)
        api.dispatch(req("ui", "/v1/session/begin",
                          gaian_id=gaian_id, human_id="human-001"))
        r = api.dispatch(req("ui", "/v1/session/end", gaian_id=gaian_id))
        assert r.success
        assert r.payload["turns"] >= 0


class TestMiddleware:
    def test_middleware_can_short_circuit(self, live_api):
        api, *_ = live_api
        api.add_middleware(lambda r: APIResponse.error(
            APIErrorCode.PERMISSION_DENIED, "Blocked by middleware."
        ))
        r = api.dispatch(req("ui", "/v1/os/status"))
        assert not r.success
        assert r.code == APIErrorCode.PERMISSION_DENIED

    def test_middleware_passthrough(self, live_api):
        api, *_ = live_api
        called = []
        api.add_middleware(lambda r: called.append(r.endpoint) or None)
        api.dispatch(req("ui", "/v1/os/version"))
        assert "/v1/os/version" in called
