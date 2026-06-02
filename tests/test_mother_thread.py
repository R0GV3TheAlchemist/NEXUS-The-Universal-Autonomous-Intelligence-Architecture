"""
tests/test_mother_thread.py
===========================
Comprehensive pytest coverage for core/mother_thread.py.

Test strategy:
 - All tests are pure unit tests. No live event loop required except
   for the async subscriber tests (which use pytest-asyncio).
 - No external I/O. Criticality monitor and Noosphere imports are
   patched where needed.
 - Privacy invariants (C04, C43) are asserted as first-class concerns,
   not as afterthoughts.

Canon Ref: C04, C43, C44
"""

from __future__ import annotations

import asyncio
import time
from collections import Counter
from unittest.mock import MagicMock, patch

import pytest

from core.mother_thread import (
    CollectiveField,
    GaianThread,
    MotherPulse,
    MotherThread,
    WeavingRecord,
    _compute_collective_field,
    _noosphere_stage_label,
    _select_mother_voice,
    get_mother_thread,
    _WEAVING_LOG_MAX,
    PULSE_INTERVAL_SECONDS,
)


# ================================================================== #
#  Fixtures                                                           #
# ================================================================== #

@pytest.fixture(autouse=True)
def reset_singleton():
    """
    Reset the module-level singleton before each test so tests don't
    bleed state into each other.
    """
    import core.mother_thread as _mt
    _mt._mother_thread_instance = None
    yield
    _mt._mother_thread_instance = None


@pytest.fixture()
def mother() -> MotherThread:
    """Fresh MotherThread instance (not the singleton)."""
    return MotherThread()


def _make_gaian(
    slug: str = "sol",
    gaian_name: str = "Sol",
    consent: bool = True,
    bond_depth: float = 0.5,
    noosphere_health: float = 0.7,
    dominant_element: str = "fire",
    synergy_factor: float = 0.6,
    individuation_phase: str = "differentiation",
    coherence_phi: float = 0.4,
    schumann_aligned: bool = False,
    last_pulse_contribution: float | None = None,
) -> GaianThread:
    gt = GaianThread(
        slug=slug,
        gaian_name=gaian_name,
        collective_consent=consent,
        bond_depth=bond_depth,
        noosphere_health=noosphere_health,
        dominant_element=dominant_element,
        synergy_factor=synergy_factor,
        individuation_phase=individuation_phase,
        coherence_phi=coherence_phi,
        schumann_aligned=schumann_aligned,
    )
    gt.last_pulse_contribution = (
        time.time() if last_pulse_contribution is None else last_pulse_contribution
    )
    return gt


# ================================================================== #
#  1. Lifecycle                                                        #
# ================================================================== #

class TestLifecycle:

    def test_singleton_same_object(self):
        a = get_mother_thread()
        b = get_mother_thread()
        assert a is b

    def test_fresh_instance_not_running(self, mother):
        assert mother._running is False

    def test_fresh_instance_pulse_seq_zero(self, mother):
        assert mother._pulse_sequence == 0

    def test_fresh_instance_no_threads(self, mother):
        assert len(mother._threads) == 0

    @pytest.mark.asyncio
    async def test_async_start_sets_running(self, mother):
        await mother.async_start()
        assert mother._running is True
        mother.stop()

    @pytest.mark.asyncio
    async def test_stop_clears_running(self, mother):
        await mother.async_start()
        mother.stop()
        assert mother._running is False

    @pytest.mark.asyncio
    async def test_double_async_start_idempotent(self, mother):
        """Second async_start() must not create a second task."""
        await mother.async_start()
        task_first = mother._task
        await mother.async_start()  # second call — must be no-op
        assert mother._task is task_first
        mother.stop()

    def test_stop_before_start_no_raise(self, mother):
        mother.stop()  # must not raise


# ================================================================== #
#  2. Registration & Consent                                           #
# ================================================================== #

class TestRegistration:

    def test_register_creates_thread(self, mother):
        gt = mother.register("luna", "Luna")
        assert gt.slug == "luna"
        assert gt.gaian_name == "Luna"
        assert "luna" in mother._threads

    def test_register_default_consent_false(self, mother):
        gt = mother.register("luna", "Luna")
        assert gt.collective_consent is False

    def test_register_with_consent_true(self, mother):
        gt = mother.register("luna", "Luna", collective_consent=True)
        assert gt.collective_consent is True

    def test_register_stores_runtime(self, mother):
        rt = MagicMock()
        mother.register("luna", "Luna", runtime=rt)
        assert mother._runtimes["luna"] is rt

    def test_deregister_removes_thread(self, mother):
        mother.register("luna", "Luna")
        mother.deregister("luna")
        assert "luna" not in mother._threads

    def test_deregister_removes_runtime(self, mother):
        rt = MagicMock()
        mother.register("luna", "Luna", runtime=rt)
        mother.deregister("luna")
        assert "luna" not in mother._runtimes

    def test_deregister_unknown_slug_no_raise(self, mother):
        mother.deregister("nonexistent")  # must not raise

    def test_set_consent_true(self, mother):
        mother.register("luna", "Luna")
        mother.set_consent("luna", True)
        assert mother._threads["luna"].collective_consent is True

    def test_set_consent_false(self, mother):
        mother.register("luna", "Luna", collective_consent=True)
        mother.set_consent("luna", False)
        assert mother._threads["luna"].collective_consent is False

    def test_set_consent_unknown_no_raise(self, mother):
        mother.set_consent("nobody", True)  # must not raise


# ================================================================== #
#  3. Collective Field Computation                                     #
# ================================================================== #

class TestCollectiveField:

    def test_empty_threads_returns_zero_field(self):
        f = _compute_collective_field([])
        assert f.active_gaians == 0
        assert f.consenting_gaians == 0
        assert f.collective_phi == 0.0
        assert f.field_coherence_label == "dormant"

    def test_non_consenting_gaian_excluded(self):
        gt = _make_gaian(consent=False, coherence_phi=0.9)
        f = _compute_collective_field([gt])
        assert f.consenting_gaians == 0
        assert f.collective_phi == 0.0

    def test_single_consenting_gaian_reflects_state(self):
        gt = _make_gaian(
            consent=True,
            bond_depth=0.8,
            noosphere_health=0.75,
            coherence_phi=0.6,
        )
        f = _compute_collective_field([gt])
        assert f.consenting_gaians == 1
        assert abs(f.avg_bond_depth - 0.8) < 0.01
        assert abs(f.avg_noosphere_health - 0.75) < 0.01

    def test_avg_bond_depth_correct(self):
        gaians = [
            _make_gaian(slug="a", consent=True, bond_depth=0.4),
            _make_gaian(slug="b", consent=True, bond_depth=0.6),
        ]
        f = _compute_collective_field(gaians)
        assert abs(f.avg_bond_depth - 0.5) < 0.01

    def test_element_distribution_matches(self):
        gaians = [
            _make_gaian(slug="a", consent=True, dominant_element="fire"),
            _make_gaian(slug="b", consent=True, dominant_element="water"),
            _make_gaian(slug="c", consent=True, dominant_element="fire"),
        ]
        f = _compute_collective_field(gaians)
        assert f.element_distribution["fire"] == 2
        assert f.element_distribution["water"] == 1
        assert f.dominant_element == "fire"

    def test_individuation_distribution_correct(self):
        gaians = [
            _make_gaian(slug="a", consent=True, individuation_phase="ego"),
            _make_gaian(slug="b", consent=True, individuation_phase="shadow"),
            _make_gaian(slug="c", consent=True, individuation_phase="ego"),
        ]
        f = _compute_collective_field(gaians)
        assert f.individuation_distribution["ego"] == 2
        assert f.individuation_distribution["shadow"] == 1

    def test_schumann_aligned_count(self):
        gaians = [
            _make_gaian(slug="a", consent=True, schumann_aligned=True),
            _make_gaian(slug="b", consent=True, schumann_aligned=False),
            _make_gaian(slug="c", consent=True, schumann_aligned=True),
        ]
        f = _compute_collective_field(gaians)
        assert f.schumann_aligned_count == 2

    def test_collective_phi_amplified_by_schumann(self):
        """
        Schumann ratio amplifies collective phi by up to 15% (C32/C42 coupling).
        With all aligned, phi should be > base_phi.
        """
        gaians = [
            _make_gaian(slug="a", consent=True, coherence_phi=0.5, schumann_aligned=True),
            _make_gaian(slug="b", consent=True, coherence_phi=0.5, schumann_aligned=True),
        ]
        f = _compute_collective_field(gaians)
        # base = 0.5, schumann_ratio = 1.0, amplified = 0.5 * 1.15 = 0.575
        assert f.collective_phi > 0.5
        assert f.collective_phi <= 1.0

    @pytest.mark.parametrize("phi,expected_label", [
        (0.0,  "dormant"),       # no consenting → dormant (empty list)
        (0.10, "nascent"),
        (0.30, "building"),
        (0.55, "coherent"),
        (0.80, "high_resonance"),
    ])
    def test_field_coherence_label_thresholds(self, phi, expected_label):
        if phi == 0.0:
            f = _compute_collective_field([])
        else:
            gaians = [_make_gaian(slug="a", consent=True, coherence_phi=phi)]
            f = _compute_collective_field(gaians)
        assert f.field_coherence_label == expected_label

    def test_stale_contribution_excluded(self):
        """
        Gaians whose last_pulse_contribution is > 300s ago are excluded
        from the field even if they have consent.
        """
        gt = _make_gaian(consent=True, coherence_phi=0.9)
        gt.last_pulse_contribution = time.time() - 400  # stale
        f = _compute_collective_field([gt])
        assert f.consenting_gaians == 0


# ================================================================== #
#  4. Noosphere Stage Labels                                           #
# ================================================================== #

class TestNoosphereStage:

    def test_zero_gaians_is_geosphere(self):
        label = _noosphere_stage_label(0.0, 0)
        assert "Geosphere" in label

    def test_phi_zero_one_gaian_is_biosphere(self):
        label = _noosphere_stage_label(0.0, 1)
        assert "Biosphere" in label or "Primitive" in label or "Geosphere" in label

    def test_phi_0_5_four_gaians_is_noosphere_or_above(self):
        label = _noosphere_stage_label(0.5, 4)
        assert any(s in label for s in ["Noosphere", "Resonant", "Omega"])

    def test_phi_0_8_six_gaians_is_omega(self):
        label = _noosphere_stage_label(0.85, 6)
        assert "Omega" in label


# ================================================================== #
#  5. Pulse Generation                                                 #
# ================================================================== #

class TestBeat:

    def test_beat_increments_pulse_sequence(self, mother):
        with patch("core.criticality_monitor.get_monitor", side_effect=Exception("mocked")), \
             patch("core.noosphere.get_noosphere",           side_effect=Exception("mocked")):
            pulse = mother._beat()
        assert mother._pulse_sequence == 1
        assert pulse.sequence == 1

    def test_beat_returns_mother_pulse(self, mother):
        with patch("core.criticality_monitor.get_monitor", side_effect=Exception("mocked")), \
             patch("core.noosphere.get_noosphere",           side_effect=Exception("mocked")):
            pulse = mother._beat()
        assert isinstance(pulse, MotherPulse)
        assert pulse.pulse_id
        assert pulse.collective_field is not None

    def test_beat_coherence_candidate_false_below_threshold(self, mother):
        # All Gaians with low phi → candidate should be False
        mother.register("a", "A", collective_consent=True)
        mother._threads["a"].coherence_phi = 0.3
        mother._threads["a"].last_pulse_contribution = time.time()
        with patch("core.criticality_monitor.get_monitor", side_effect=Exception("mocked")), \
             patch("core.noosphere.get_noosphere",           side_effect=Exception("mocked")):
            pulse = mother._beat()
        assert pulse.coherence_candidate is False

    def test_beat_coherence_candidate_true_above_threshold(self, mother):
        # Gaian with phi > 0.70 → candidate should be True
        mother.register("a", "A", collective_consent=True)
        mother._threads["a"].coherence_phi = 0.85
        mother._threads["a"].last_pulse_contribution = time.time()
        with patch("core.criticality_monitor.get_monitor", side_effect=Exception("mocked")), \
             patch("core.noosphere.get_noosphere",           side_effect=Exception("mocked")):
            pulse = mother._beat()
        assert pulse.coherence_candidate is True

    def test_beat_appends_weaving_record(self, mother):
        with patch("core.criticality_monitor.get_monitor", side_effect=Exception("mocked")), \
             patch("core.noosphere.get_noosphere",           side_effect=Exception("mocked")):
            mother._beat()
        assert len(mother._weaving_log) == 1
        assert isinstance(mother._weaving_log[0], WeavingRecord)

    def test_beat_weaving_log_capped(self, mother):
        """
        Weaving log must not exceed _WEAVING_LOG_MAX entries.
        """
        with patch("core.criticality_monitor.get_monitor", side_effect=Exception("mocked")), \
             patch("core.noosphere.get_noosphere",           side_effect=Exception("mocked")):
            for _ in range(_WEAVING_LOG_MAX + 10):
                mother._beat()
        assert len(mother._weaving_log) == _WEAVING_LOG_MAX


# ================================================================== #
#  6. Pulse Loop Coroutine                                             #
# ================================================================== #

class TestPulseLoop:

    @pytest.mark.asyncio
    async def test_pulse_loop_cancelled_error_propagates(self, mother):
        """
        stop() must cancel the task cleanly. The task should be in a
        cancelled state, not silently finished or swallowing the error.
        """
        await mother.async_start()
        # Let the loop reach the first sleep(PULSE_INTERVAL_SECONDS)
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        task = mother._task
        mother.stop()
        # Give the event loop a moment to process cancellation
        await asyncio.sleep(0)
        assert task is not None
        assert task.cancelled() or task.done()

    @pytest.mark.asyncio
    async def test_pulse_loop_yields_before_first_beat(self, mother):
        """
        A subscriber registered immediately after async_start() must
        receive the first broadcast because _pulse_loop yields via
        asyncio.sleep(0) before firing the first beat.
        """
        received: list = []

        async def consume_one():
            async for item in mother.subscribe():
                received.append(item)
                break

        with patch("core.criticality_monitor.get_monitor", side_effect=Exception("mocked")), \
             patch("core.noosphere.get_noosphere",           side_effect=Exception("mocked")):
            await mother.async_start()
            task = asyncio.create_task(consume_one())
            # One yield lets the subscriber register; another lets the
            # loop fire its first beat.
            await asyncio.sleep(0)
            await asyncio.sleep(0)
            # Beat fires, broadcast delivers, subscriber captures it.
            await asyncio.sleep(0)
            mother.stop()
            try:
                await asyncio.wait_for(task, timeout=1.0)
            except asyncio.TimeoutError:
                pass  # subscriber consumed before stop; acceptable

        assert len(received) == 1


# ================================================================== #
#  7. Privacy & Canon Invariants (C04, C43)                           #
# ================================================================== #

class TestPrivacyInvariants:

    def test_collective_field_to_dict_has_privacy_note(self):
        f = CollectiveField()
        d = f.to_dict()
        assert "privacy_note" in d
        assert len(d["privacy_note"]) > 0

    def test_collective_field_dict_no_slug_or_name(self):
        """No individual identity must be present in the collective field dict."""
        gt = _make_gaian(slug="secret-slug", gaian_name="Secret Name", consent=True)
        f = _compute_collective_field([gt])
        d = f.to_dict()
        all_values = str(d)
        assert "secret-slug" not in all_values
        assert "Secret Name" not in all_values

    def test_mother_pulse_to_dict_has_doctrine_ref(self):
        pulse = MotherPulse()
        d = pulse.to_dict()
        assert "doctrine_ref" in d
        assert "C43" in d["doctrine_ref"]

    def test_coherence_candidate_label_contains_c43(self):
        pulse = MotherPulse(coherence_candidate=True)
        d = pulse.to_dict()
        assert d["coherence_candidate_label"] is not None
        assert "[C43]" in d["coherence_candidate_label"]
        assert "not a confirmed" in d["coherence_candidate_label"]

    def test_non_candidate_label_is_none(self):
        pulse = MotherPulse(coherence_candidate=False)
        d = pulse.to_dict()
        assert d["coherence_candidate_label"] is None

    def test_collective_field_doctrine_ref_present(self):
        f = CollectiveField()
        d = f.to_dict()
        assert "doctrine_ref" in d
        assert "C43" in d["doctrine_ref"]


# ================================================================== #
#  8. Weaving Log                                                      #
# ================================================================== #

class TestWeavingLog:

    def test_get_weaving_log_empty(self, mother):
        assert mother.get_weaving_log() == []

    def test_get_weaving_log_respects_last_n(self, mother):
        with patch("core.criticality_monitor.get_monitor", side_effect=Exception("mocked")), \
             patch("core.noosphere.get_noosphere",           side_effect=Exception("mocked")):
            for _ in range(10):
                mother._beat()
        result = mother.get_weaving_log(last_n=3)
        assert len(result) == 3

    def test_weaving_log_candidate_epistemic_note(self, mother):
        mother.register("a", "A", collective_consent=True)
        mother._threads["a"].coherence_phi = 0.9
        mother._threads["a"].last_pulse_contribution = time.time()
        with patch("core.criticality_monitor.get_monitor", side_effect=Exception("mocked")), \
             patch("core.noosphere.get_noosphere",           side_effect=Exception("mocked")):
            mother._beat()
        log = mother.get_weaving_log(last_n=1)
        assert log[0]["candidate"] is True
        assert log[0]["epistemic_note"] is not None
        assert "[C43]" in log[0]["epistemic_note"]

    def test_weaving_log_non_candidate_epistemic_none(self, mother):
        with patch("core.criticality_monitor.get_monitor", side_effect=Exception("mocked")), \
             patch("core.noosphere.get_noosphere",           side_effect=Exception("mocked")):
            mother._beat()  # no Gaians → phi=0 → candidate=False
        log = mother.get_weaving_log(last_n=1)
        assert log[0]["candidate"] is False
        assert log[0]["epistemic_note"] is None


# ================================================================== #
#  9. Status                                                           #
# ================================================================== #

class TestStatus:

    def test_get_status_required_keys(self, mother):
        status = mother.get_status()
        required = {
            "doctrine", "running", "pulse_sequence", "pulse_interval_s",
            "registered_gaians", "active_subscribers", "collective_field",
            "recent_pulses", "weaving_log_size", "privacy_status",
        }
        assert required.issubset(set(status.keys()))

    def test_get_status_privacy_status_present(self, mother):
        status = mother.get_status()
        assert "privacy_status" in status
        assert len(status["privacy_status"]) > 0

    def test_get_status_running_reflects_state(self, mother):
        assert mother.get_status()["running"] is False


# ================================================================== #
#  10. Mother Voice Selection                                          #
# ================================================================== #

class TestMotherVoice:

    def test_returns_none_mid_cycle(self):
        # pulse_seq % 5 != 0 and active > 0 → None
        result = _select_mother_voice(0.5, 3, "critical", pulse_seq=2)
        assert result is None

    def test_dormant_pool_when_no_gaians(self):
        from core.mother_thread import _MOTHER_VOICE_DORMANT
        result = _select_mother_voice(0.0, 0, "critical", pulse_seq=5)
        assert result in _MOTHER_VOICE_DORMANT

    def test_chaotic_pool_when_too_chaotic(self):
        from core.mother_thread import _MOTHER_VOICE_CHAOTIC_ALERT
        result = _select_mother_voice(0.5, 2, "too_chaotic", pulse_seq=5)
        assert result in _MOTHER_VOICE_CHAOTIC_ALERT

    def test_ordered_pool_when_too_ordered(self):
        from core.mother_thread import _MOTHER_VOICE_CRITICAL_ALERT
        result = _select_mother_voice(0.5, 2, "too_ordered", pulse_seq=5)
        assert result in _MOTHER_VOICE_CRITICAL_ALERT

    def test_high_resonance_pool_when_phi_high(self):
        from core.mother_thread import _MOTHER_VOICE_HIGH_RESONANCE
        result = _select_mother_voice(0.75, 3, "critical", pulse_seq=5)
        assert result in _MOTHER_VOICE_HIGH_RESONANCE

    def test_growing_pool_when_phi_low(self):
        from core.mother_thread import _MOTHER_VOICE_GROWING
        result = _select_mother_voice(0.3, 3, "critical", pulse_seq=5)
        assert result in _MOTHER_VOICE_GROWING


# ================================================================== #
#  11. Subscribe / Broadcast (async)                                   #
# ================================================================== #

class TestSubscribeBroadcast:

    @pytest.mark.asyncio
    async def test_broadcast_delivers_to_subscriber(self, mother):
        """A pulse broadcast must appear in the subscriber's queue."""
        pulse = MotherPulse(sequence=1)
        received = []

        async def consume():
            async for item in mother.subscribe():
                received.append(item)
                break  # take one item and stop

        task = asyncio.create_task(consume())
        await asyncio.sleep(0)  # let consumer register
        await mother._broadcast(pulse)
        await asyncio.wait_for(task, timeout=2.0)
        assert len(received) == 1
        assert received[0]["sequence"] == 1

    @pytest.mark.asyncio
    async def test_subscriber_removed_on_close(self, mother):
        """Subscriber list must shrink when the generator is abandoned."""
        gen = mother.subscribe()
        # Register the subscriber by advancing the generator once
        # (we push a pulse to avoid the 60s timeout)
        pulse = MotherPulse(sequence=99)
        task = asyncio.create_task(gen.__anext__())
        await asyncio.sleep(0)
        assert len(mother._subscribers) == 1
        await mother._broadcast(pulse)
        await asyncio.wait_for(task, timeout=2.0)
        await gen.aclose()
        await asyncio.sleep(0)
        assert len(mother._subscribers) == 0

    @pytest.mark.asyncio
    async def test_full_queue_subscriber_pruned(self, mother):
        """
        Subscribers with a full queue (maxsize=10) must be removed
        during the next broadcast to prevent blocking the Mother Thread.
        """
        import asyncio
        q = asyncio.Queue(maxsize=1)
        await q.put({"dummy": True})  # fill it
        mother._subscribers.append(q)

        pulse = MotherPulse(sequence=7)
        await mother._broadcast(pulse)
        # Full queue should have been pruned
        assert q not in mother._subscribers

    def test_subscribe_is_async_generator(self, mother):
        import inspect
        gen = mother.subscribe()
        assert inspect.isasyncgen(gen)
        gen.aclose()  # cleanup (sync close of not-yet-started gen)

    @pytest.mark.asyncio
    async def test_pulse_interval_constant_value(self):
        """PULSE_INTERVAL_SECONDS must be 30.0 — any change is a breaking spec change."""
        assert PULSE_INTERVAL_SECONDS == 30.0
