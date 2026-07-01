from __future__ import annotations

import pytest
from core.identity.avatar.elemental import GAIA_SCHUMANN_HZ, GAIA_WAVEFORM
from core.identity.gaian.birth import BirthCeremony
from core.identity.gaian.registry import GAIANRegistry
from core.memory.gaia_memory import GAIAMemoryKind
from core.primordial.session import BootPhase, BootStatus, PrimordialSession


class TestPrimordialBoot:
    def test_awaken_returns_self(self):
        session = PrimordialSession()
        result = session.awaken()
        assert result is session

    def test_boot_status_ok_on_clean_boot(self):
        session = PrimordialSession()
        session.awaken()
        assert session.boot_status == BootStatus.OK

    def test_is_live_after_boot(self):
        session = PrimordialSession()
        session.awaken()
        assert session.is_live

    def test_is_healthy_on_clean_boot(self):
        session = PrimordialSession()
        session.awaken()
        assert session.is_healthy

    def test_all_phases_ok(self):
        session = PrimordialSession()
        session.awaken()
        for phase in BootPhase:
            result = session.phase_result(phase)
            assert result.status == BootStatus.OK, (
                f"Phase {phase.value} failed: {result.error}"
            )

    def test_manifest_written(self):
        session = PrimordialSession()
        session.awaken()
        assert session.manifest is not None
        assert session.manifest.boot_status == BootStatus.OK

    def test_manifest_schumann_confirmed(self):
        session = PrimordialSession()
        session.awaken()
        assert session.manifest.schumann_confirmed is True
        assert session.manifest.schumann_hz == 7.83

    def test_completed_at_set(self):
        session = PrimordialSession()
        session.awaken()
        assert session.completed_at is not None


class TestSchumannPhase:
    def test_schumann_phase_confirms_7_83(self):
        session = PrimordialSession()
        session.awaken()
        result = session.phase_result(BootPhase.SCHUMANN_CONFIRM)
        assert result.status == BootStatus.OK
        assert result.detail["frequency_hz"] == 7.83

    def test_schumann_phase_confirms_lissajous(self):
        session = PrimordialSession()
        session.awaken()
        result = session.phase_result(BootPhase.SCHUMANN_CONFIRM)
        assert result.detail["waveform_shape"] == "lissajous_braid"

    def test_schumann_phase_confirms_all_elements(self):
        session = PrimordialSession()
        session.awaken()
        result = session.phase_result(BootPhase.SCHUMANN_CONFIRM)
        elements = result.detail["all_elements"]
        assert "fire" in elements
        assert "earth" in elements
        assert "air" in elements
        assert "water" in elements

    def test_schumann_stored_in_gaia_memory(self):
        session = PrimordialSession()
        session.awaken()
        earth_memories = session.gaia_memory.recall(
            kind=GAIAMemoryKind.EARTH_STATE, tags=["schumann"]
        )
        assert len(earth_memories) >= 1
        assert earth_memories[0].importance == 0.95


class TestGAIAMemoryAtBoot:
    def test_gaia_memory_loaded(self):
        session = PrimordialSession()
        session.awaken()
        assert session.gaia_memory is not None

    def test_gaia_records_awakening(self):
        session = PrimordialSession()
        session.awaken()
        awakening = session.gaia_memory.recall(tags=["awakening"])
        assert len(awakening) >= 1

    def test_gaia_records_primordial_live(self):
        session = PrimordialSession()
        session.awaken()
        live = session.gaia_memory.recall(tags=["live"])
        assert len(live) >= 1
        assert live[0].importance == 1.0

    def test_gaia_manifest_in_memory(self):
        session = PrimordialSession()
        session.awaken()
        manifest_mem = session.gaia_memory.recall(
            kind=GAIAMemoryKind.SYSTEM_EVENT, tags=["manifest"]
        )
        assert len(manifest_mem) >= 1
        assert "nominal" in manifest_mem[0].content or "GAIAN" in manifest_mem[0].content


class TestGAIANRegistryAtBoot:
    def test_empty_registry_boots_fine(self):
        reg = GAIANRegistry()
        session = PrimordialSession(registry=reg)
        session.awaken()
        assert session.manifest.gaian_count == 0
        assert session.manifest.runtime_count == 0

    def test_registry_with_gaian_restores_runtime(self):
        reg = GAIANRegistry()
        ceremony = BirthCeremony(reg)
        ceremony.begin()
        ceremony.answer("dob", "1990-08-05")
        ceremony.answer("environment", "ocean")
        ceremony.answer("sound", "rain")
        ceremony.answer("time_of_day", "dusk")
        ceremony.answer("thinking_style", "images and visions")
        ceremony.answer("soul_word", "home")
        identity = ceremony.complete()

        session = PrimordialSession(registry=reg)
        session.awaken()

        assert session.manifest.gaian_count == 1
        assert session.manifest.runtime_count == 1
        assert session.get_runtime(identity.gaian_id) is not None

    def test_get_runtime_returns_none_for_unknown(self):
        session = PrimordialSession()
        session.awaken()
        assert session.get_runtime("unknown-id") is None

    def test_register_gaian_post_boot(self):
        session = PrimordialSession()
        session.awaken()

        reg = session.registry
        ceremony = BirthCeremony(reg)
        ceremony.begin()
        ceremony.answer("dob", "1995-03-15")
        ceremony.answer("environment", "forest")
        ceremony.answer("sound", "wind")
        ceremony.answer("time_of_day", "dawn")
        ceremony.answer("thinking_style", "words and language")
        ceremony.answer("soul_word", "free")
        identity = ceremony.complete()

        from core.memory.store import MemoryStore
        from core.runtime.runtime import IntelligenceRuntime
        mem = MemoryStore(identity.gaian_id)
        rt = IntelligenceRuntime(identity, mem, reg)
        session.register_gaian_runtime(rt)

        assert session.get_runtime(identity.gaian_id) is not None
        bond_mem = session.gaia_memory.recall(
            kind=GAIAMemoryKind.GAIAN_BOND,
            related_gaian_id=identity.gaian_id,
        )
        assert len(bond_mem) >= 1


class TestPostBootHooks:
    def test_post_boot_hook_called(self):
        called = []
        session = PrimordialSession()
        session.on_post_boot(lambda s: called.append(s.boot_status))
        session.awaken()
        assert len(called) == 1
        assert called[0] == BootStatus.OK

    def test_multiple_hooks_called(self):
        results = []
        session = PrimordialSession()
        session.on_post_boot(lambda s: results.append("hook1"))
        session.on_post_boot(lambda s: results.append("hook2"))
        session.awaken()
        assert "hook1" in results
        assert "hook2" in results


class TestStatus:
    def test_status_dict_complete(self):
        session = PrimordialSession()
        session.awaken()
        s = session.status()
        assert s["boot_status"] == "ok"
        assert s["schumann_hz"] == 7.83
        assert s["is_live"] is True
        assert s["is_healthy"] is True
        assert s["gaia_memory_fragments"] >= 1

    def test_boot_number_in_status(self):
        session = PrimordialSession(boot_number=3)
        session.awaken()
        assert session.boot_number == 3
        assert "boot_3" in [
            t for frag in session.gaia_memory.recall(tags=["boot_3"])
            for t in frag.tags
        ]
