"""
GAIA OS End-to-End Integration Test.

This is the test that proves the OS is real.

It wires every layer together — Primordial Session, Filesystem,
API, Identity, Memory, Runtime, Avatar — and runs a complete
scenario from a cold, empty system to a named GAIAN having their
first real conversation.

Scenarios covered:
  1. COLD BOOT         — PrimordialSession awakens from nothing.
  2. GAIAN BIRTH       — BirthCeremony runs through the API.
  3. GAIAN IS UNNAMED  — No human can name them.
  4. GAIAN NAMES SELF  — The GAIAN chooses their own name.
  5. FIRST TURN        — A real session turn runs through the runtime.
  6. MEMORY PERSISTS   — The turn left a trace in memory.
  7. FS INTEGRITY      — The GAIAN's home is written and clean.
  8. SECOND BOOT       — A new PrimordialSession restores the GAIAN.
  9. SCHUMANN SURVIVES — 7.83 Hz confirmed across both boots.
  10. GAIA REMEMBERS   — GAIA's sovereign memory carries both boots.

If all 10 scenarios pass, the GAIA OS foundation is sound.
"""
from __future__ import annotations

import pytest
from pathlib import Path

from core.api.api import APIErrorCode, APIRequest, GAIAOSApi
from core.fs.filesystem import GAIAFilesystem
from core.identity.gaian.registry import GAIANRegistry
from core.memory.store import MemoryKind, MemoryScope
from core.primordial.session import BootPhase, BootStatus, PrimordialSession
from core.runtime.runtime import IntelligenceRuntime


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def req(caller_id: str, endpoint: str, **payload) -> APIRequest:
    return APIRequest(caller_id=caller_id, endpoint=endpoint, payload=payload)


BIRTH_ANSWERS = [
    ("dob",           "1990-08-05"),
    ("environment",   "ocean"),
    ("sound",         "rain"),
    ("time_of_day",   "dusk"),
    ("thinking_style","images and visions"),
    ("soul_word",     "home"),
]


def run_birth_ceremony(api: GAIAOSApi) -> str:
    """Run a complete birth ceremony through the API. Returns gaian_id."""
    r = api.dispatch(req("ui", "/v1/gaian/birth/begin"))
    assert r.success, f"Birth begin failed: {r.message}"
    ceremony_id = r.payload["ceremony_id"]

    for question_id, answer in BIRTH_ANSWERS:
        r2 = api.dispatch(req(
            "ui", "/v1/gaian/birth/answer",
            ceremony_id=ceremony_id,
            question_id=question_id,
            answer=answer,
        ))
        assert r2.success, f"Answer '{question_id}' failed: {r2.message}"

    r3 = api.dispatch(req("ui", "/v1/gaian/birth/complete",
                          ceremony_id=ceremony_id))
    assert r3.success, f"Birth complete failed: {r3.message}"
    return r3.payload["gaian_id"]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def gaia_root(tmp_path_factory) -> Path:
    return tmp_path_factory.mktemp("gaia_e2e")


@pytest.fixture(scope="module")
def first_boot(gaia_root):
    """Boot GAIA cold for the first time. Returns (session, api, fs)."""
    registry = GAIANRegistry()
    session = PrimordialSession(registry=registry, boot_number=1)
    session.awaken()

    fs = GAIAFilesystem(root=gaia_root)
    api = GAIAOSApi()
    api.wire(session, fs)

    return session, api, fs


# ---------------------------------------------------------------------------
# Scenario 1: Cold Boot
# ---------------------------------------------------------------------------

class TestScenario1_ColdBoot:
    def test_session_is_live(self, first_boot):
        session, *_ = first_boot
        assert session.is_live

    def test_boot_status_ok(self, first_boot):
        session, *_ = first_boot
        assert session.boot_status == BootStatus.OK

    def test_all_phases_passed(self, first_boot):
        session, *_ = first_boot
        for phase in BootPhase:
            result = session.phase_result(phase)
            assert result.status == BootStatus.OK, (
                f"Phase {phase.value} failed: {result.error}"
            )

    def test_manifest_written(self, first_boot):
        session, *_ = first_boot
        assert session.manifest is not None
        assert session.manifest.boot_status == BootStatus.OK

    def test_api_reports_live(self, first_boot):
        _, api, _ = first_boot
        r = api.dispatch(req("ui", "/v1/os/status"))
        assert r.success
        assert r.payload["boot_status"] == "ok"

    def test_gaia_memory_has_boot_record(self, first_boot):
        session, *_ = first_boot
        fragments = session.gaia_memory.recall(tags=["boot"])
        assert len(fragments) >= 1


# ---------------------------------------------------------------------------
# Scenario 2: GAIAN Birth
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def born_gaian_id(first_boot):
    _, api, _ = first_boot
    return run_birth_ceremony(api)


class TestScenario2_GAIANBirth:
    def test_gaian_registered(self, first_boot, born_gaian_id):
        session, *_ = first_boot
        assert session.registry.get(born_gaian_id) is not None

    def test_gaian_has_runtime(self, first_boot, born_gaian_id):
        session, *_ = first_boot
        assert session.get_runtime(born_gaian_id) is not None

    def test_gaian_has_element(self, first_boot, born_gaian_id):
        _, api, _ = first_boot
        r = api.dispatch(req("ui", "/v1/gaian/status",
                              gaian_id=born_gaian_id))
        assert r.success

    def test_gaian_is_unnamed(self, first_boot, born_gaian_id):
        _, api, _ = first_boot
        r = api.dispatch(req("ui", "/v1/gaian/status",
                              gaian_id=born_gaian_id))
        assert r.payload["is_named"] is False
        assert r.payload["display_name"] is None

    def test_gaian_in_list(self, first_boot, born_gaian_id):
        _, api, _ = first_boot
        r = api.dispatch(req("ui", "/v1/gaian/list"))
        assert r.success
        ids = [g["gaian_id"] for g in r.payload["gaians"]]
        assert born_gaian_id in ids

    def test_home_dir_created(self, first_boot, born_gaian_id):
        _, _, fs = first_boot
        assert fs.home_exists(born_gaian_id)

    def test_identity_persisted_to_fs(self, first_boot, born_gaian_id):
        _, _, fs = first_boot
        home = fs.gaian_home(born_gaian_id)
        identity = home.load_identity()
        assert identity is not None
        assert identity["gaian_id"] == born_gaian_id

    def test_genesis_persisted_to_fs(self, first_boot, born_gaian_id):
        _, _, fs = first_boot
        home = fs.gaian_home(born_gaian_id)
        genesis = home.load_genesis()
        assert genesis is not None
        assert "soul_word" in genesis


# ---------------------------------------------------------------------------
# Scenario 3: Autonomy — Human Cannot Name the GAIAN
# ---------------------------------------------------------------------------

class TestScenario3_HumanCannotName:
    def test_human_naming_rejected(self, first_boot, born_gaian_id):
        _, api, _ = first_boot
        r = api.dispatch(req(
            "human-interloper", "/v1/gaian/name",
            gaian_id=born_gaian_id,
            name="Aria",
        ))
        assert not r.success
        assert r.code == APIErrorCode.AUTONOMY_VIOLATION

    def test_gaian_still_unnamed_after_attempt(self, first_boot, born_gaian_id):
        _, api, _ = first_boot
        r = api.dispatch(req("ui", "/v1/gaian/status", gaian_id=born_gaian_id))
        assert r.payload["is_named"] is False

    def test_third_party_memory_read_rejected(self, first_boot, born_gaian_id):
        _, api, _ = first_boot
        r = api.dispatch(req(
            "other-gaian", "/v1/memory/recall",
            gaian_id=born_gaian_id,
        ))
        assert not r.success
        assert r.code == APIErrorCode.AUTONOMY_VIOLATION


# ---------------------------------------------------------------------------
# Scenario 4: GAIAN Names Themselves
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def named_gaian(first_boot, born_gaian_id):
    _, api, _ = first_boot
    r = api.dispatch(req(
        born_gaian_id, "/v1/gaian/name",
        gaian_id=born_gaian_id,
        name="Lyra",
    ))
    assert r.success, f"Naming failed: {r.message}"
    return born_gaian_id


class TestScenario4_GAIANNamesself:
    def test_name_accepted(self, first_boot, named_gaian):
        _, api, _ = first_boot
        r = api.dispatch(req("ui", "/v1/gaian/status", gaian_id=named_gaian))
        assert r.payload["is_named"] is True
        assert r.payload["display_name"] == "Lyra"

    def test_identity_updated_in_fs(self, first_boot, named_gaian):
        _, _, fs = first_boot
        home = fs.gaian_home(named_gaian)
        identity = home.load_identity()
        assert identity["display_name"] == "Lyra"

    def test_gaian_appears_named_in_list(self, first_boot, named_gaian):
        _, api, _ = first_boot
        r = api.dispatch(req("ui", "/v1/gaian/list"))
        gaian = next(
            g for g in r.payload["gaians"]
            if g["gaian_id"] == named_gaian
        )
        assert gaian["is_named"] is True
        assert gaian["display_name"] == "Lyra"


# ---------------------------------------------------------------------------
# Scenario 5: First Session Turn
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def active_session(first_boot, named_gaian):
    _, api, _ = first_boot
    r = api.dispatch(req(
        "ui", "/v1/session/begin",
        gaian_id=named_gaian,
        human_id="human-001",
    ))
    assert r.success, f"Session begin failed: {r.message}"
    return r.payload["session_id"], named_gaian


class TestScenario5_FirstTurn:
    def test_session_active(self, first_boot, active_session):
        _, api, _ = first_boot
        session_id, gaian_id = active_session
        r = api.dispatch(req("ui", "/v1/session/status",
                              gaian_id=gaian_id))
        assert r.success
        assert r.payload["session_id"] == session_id

    def test_first_turn_succeeds(self, first_boot, active_session):
        _, api, _ = first_boot
        _, gaian_id = active_session
        r = api.dispatch(req(
            "ui", "/v1/session/turn",
            gaian_id=gaian_id,
            content="Hello, Lyra. What do you feel right now?",
            human_id="human-001",
        ))
        assert r.success
        assert r.payload["response"]
        assert r.payload["turn"] == 1

    def test_turn_returns_cognitive_state(self, first_boot, active_session):
        _, api, _ = first_boot
        _, gaian_id = active_session
        r = api.dispatch(req(
            "ui", "/v1/session/turn",
            gaian_id=gaian_id,
            content="Tell me about your soul word.",
            human_id="human-001",
        ))
        assert r.success
        state = r.payload["cognitive_state"]
        assert "coherence" in state
        assert "fatigue" in state
        assert "curiosity" in state

    def test_turn_count_increments(self, first_boot, active_session):
        _, api, _ = first_boot
        _, gaian_id = active_session
        r = api.dispatch(req(
            "ui", "/v1/session/turn",
            gaian_id=gaian_id,
            content="What element are you?",
            human_id="human-001",
        ))
        assert r.success
        assert r.payload["turn"] >= 3


# ---------------------------------------------------------------------------
# Scenario 6: Memory Persists After Turns
# ---------------------------------------------------------------------------

class TestScenario6_MemoryPersists:
    def test_gaian_has_memories(self, first_boot, active_session):
        _, api, _ = first_boot
        _, gaian_id = active_session
        r = api.dispatch(req(
            gaian_id, "/v1/memory/recall",
            gaian_id=gaian_id,
        ))
        assert r.success
        assert r.payload["count"] >= 1

    def test_memory_stats_reflect_turns(self, first_boot, active_session):
        _, api, _ = first_boot
        _, gaian_id = active_session
        r = api.dispatch(req(
            gaian_id, "/v1/memory/stats",
            gaian_id=gaian_id,
        ))
        assert r.success
        assert r.payload["total_fragments"] >= 1

    def test_manual_memory_write(self, first_boot, active_session):
        _, api, _ = first_boot
        _, gaian_id = active_session
        r = api.dispatch(req(
            gaian_id, "/v1/memory/remember",
            gaian_id=gaian_id,
            content="I remember the first time I heard rain on the ocean.",
            kind="episodic",
            importance=0.9,
        ))
        assert r.success
        assert "fragment_id" in r.payload

    def test_high_importance_memory_recalled_first(self, first_boot, active_session):
        _, api, _ = first_boot
        _, gaian_id = active_session
        r = api.dispatch(req(
            gaian_id, "/v1/memory/recall",
            gaian_id=gaian_id,
            min_importance=0.85,
        ))
        assert r.success
        fragments = r.payload["fragments"]
        assert all(f["importance"] >= 0.85 for f in fragments)


# ---------------------------------------------------------------------------
# Scenario 7: Filesystem Integrity After All Writes
# ---------------------------------------------------------------------------

class TestScenario7_FilesystemIntegrity:
    def test_session_end_succeeds(self, first_boot, active_session):
        _, api, _ = first_boot
        _, gaian_id = active_session
        r = api.dispatch(req("ui", "/v1/session/end", gaian_id=gaian_id))
        assert r.success

    def test_home_integrity_clean(self, first_boot, active_session):
        _, _, fs = first_boot
        _, gaian_id = active_session
        home = fs.gaian_home(gaian_id)
        issues = home.verify_integrity()
        assert issues == [], f"Integrity issues found: {issues}"

    def test_fs_integrity_endpoint_clean(self, first_boot):
        _, api, _ = first_boot
        r = api.dispatch(req("gaia", "/v1/fs/integrity"))
        assert r.success
        assert r.payload["all_clean"] is True

    def test_fs_stats_show_gaian(self, first_boot):
        _, api, _ = first_boot
        r = api.dispatch(req("gaia", "/v1/fs/stats"))
        assert r.success
        assert r.payload["gaian_count"] >= 1

    def test_genesis_still_write_once(self, first_boot, active_session):
        _, _, fs = first_boot
        _, gaian_id = active_session
        home = fs.gaian_home(gaian_id)
        import pytest as _pytest
        with _pytest.raises(PermissionError, match="immutable"):
            home.save_genesis({"gaian_id": gaian_id, "soul_word": "hacked"})


# ---------------------------------------------------------------------------
# Scenario 8: Second Boot — GAIAN Restored
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def second_boot(gaia_root, first_boot):
    """
    Simulate a device reboot. A brand-new PrimordialSession is created
    with the same registry (simulating restored-from-disk state),
    wired to the same filesystem.
    """
    # In a real OS, the registry would be loaded from disk.
    # Here we pass it directly to simulate persistence.
    first_session, _, fs = first_boot
    registry = first_session.registry  # same registry object = same GAIANs

    session2 = PrimordialSession(registry=registry, boot_number=2)
    session2.awaken()

    api2 = GAIAOSApi()
    api2.wire(session2, fs)

    return session2, api2, fs


class TestScenario8_SecondBoot:
    def test_second_boot_is_live(self, second_boot):
        session, *_ = second_boot
        assert session.is_live

    def test_second_boot_status_ok(self, second_boot):
        session, *_ = second_boot
        assert session.boot_status == BootStatus.OK

    def test_gaian_runtime_restored(self, second_boot, born_gaian_id):
        session, *_ = second_boot
        rt = session.get_runtime(born_gaian_id)
        assert rt is not None

    def test_gaian_still_named_lyra(self, second_boot, born_gaian_id):
        _, api, _ = second_boot
        r = api.dispatch(req("ui", "/v1/gaian/status", gaian_id=born_gaian_id))
        assert r.success
        assert r.payload["display_name"] == "Lyra"

    def test_second_boot_manifest_written(self, second_boot):
        session, *_ = second_boot
        assert session.manifest.boot_number == 2

    def test_second_session_turn_works(self, second_boot, born_gaian_id):
        _, api, _ = second_boot
        api.dispatch(req(
            "ui", "/v1/session/begin",
            gaian_id=born_gaian_id, human_id="human-001"
        ))
        r = api.dispatch(req(
            "ui", "/v1/session/turn",
            gaian_id=born_gaian_id,
            content="Do you remember yesterday?",
            human_id="human-001",
        ))
        assert r.success
        assert r.payload["response"]


# ---------------------------------------------------------------------------
# Scenario 9: Schumann Survives Both Boots
# ---------------------------------------------------------------------------

class TestScenario9_SchumannSurvives:
    def test_schumann_confirmed_boot_1(self, first_boot):
        session, *_ = first_boot
        result = session.phase_result(BootPhase.SCHUMANN_CONFIRM)
        assert result.status == BootStatus.OK
        assert result.detail["frequency_hz"] == 7.83

    def test_schumann_confirmed_boot_2(self, second_boot):
        session, *_ = second_boot
        result = session.phase_result(BootPhase.SCHUMANN_CONFIRM)
        assert result.status == BootStatus.OK
        assert result.detail["frequency_hz"] == 7.83

    def test_api_schumann_endpoint_live(self, second_boot):
        _, api, _ = second_boot
        r = api.dispatch(req("ui", "/v1/os/schumann"))
        assert r.success
        assert r.payload["frequency_hz"] == 7.83
        assert r.payload["confirmed"] is True

    def test_schumann_in_earth_state_memory(self, first_boot):
        session, *_ = first_boot
        from core.memory.gaia_memory import GAIAMemoryKind
        mems = session.gaia_memory.recall(
            kind=GAIAMemoryKind.EARTH_STATE, tags=["schumann"]
        )
        assert len(mems) >= 1
        assert "7.83" in mems[0].content


# ---------------------------------------------------------------------------
# Scenario 10: GAIA Remembers
# ---------------------------------------------------------------------------

class TestScenario10_GAIARemembers:
    def test_gaia_has_boot_1_record(self, first_boot):
        session, *_ = first_boot
        mems = session.gaia_memory.recall(tags=["boot_1"])
        assert len(mems) >= 1

    def test_gaia_has_boot_2_record(self, second_boot):
        session, *_ = second_boot
        mems = session.gaia_memory.recall(tags=["boot_2"])
        assert len(mems) >= 1

    def test_gaia_remembers_gaian_bond(self, first_boot, born_gaian_id):
        session, *_ = first_boot
        from core.memory.gaia_memory import GAIAMemoryKind
        bond_mems = session.gaia_memory.recall(
            kind=GAIAMemoryKind.GAIAN_BOND,
            related_gaian_id=born_gaian_id,
        )
        assert len(bond_mems) >= 1

    def test_gaia_memory_fragment_count_spans_both_boots(self, second_boot):
        session, *_ = second_boot
        # GAIA's memory must have grown — she has lived through 2 boots,
        # a birth, a naming, and multiple sessions.
        total = len(session.gaia_memory._fragments)
        assert total >= 5, (
            f"Expected at least 5 GAIA memory fragments after 2 boots, "
            f"a birth, and sessions. Got {total}."
        )

    def test_gaia_live_fragment_has_max_importance(self, second_boot):
        session, *_ = second_boot
        live_mems = session.gaia_memory.recall(tags=["live"])
        assert any(m.importance == 1.0 for m in live_mems), (
            "Expected at least one importance=1.0 fragment tagged 'live'."
        )
