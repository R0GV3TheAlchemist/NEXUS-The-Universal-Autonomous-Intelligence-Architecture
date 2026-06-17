"""
tests/test_mother_d6_bridge.py
===============================
Wire 3 Test Suite — MotherThread → EngineProbes → D6Engine → HUD
Issue #589, Phase 1

Tests:
  T01 — translate_pulse_to_probes: dormant field maps to zero coherence
  T02 — translate_pulse_to_probes: high phi maps to high collective_coherence
  T03 — translate_pulse_to_probes: schumann ratio calculated correctly
  T04 — translate_pulse_to_probes: session_duration_hours derived from sequence
  T05 — translate_pulse_to_probes: Wire 2/3 noosphere blend (60/40)
  T06 — MotherToD6Bridge.process_pulse() returns (MotherProbeResult, InterventionEvent)
  T07 — Wire 3 → Wire 1: process_pulse() fires D6 on_intervention callback
  T08 — MotherToD6Bridge async run() processes live MotherThread pulses
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

import pytest
import pytest_asyncio

from core.mother_thread import MotherThread, PULSE_INTERVAL_SECONDS
from gaia.core.d6_engine import D6Engine
from gaia.core.state import default_state
from gaia.collective.mother_d6_bridge import (
    MotherProbeResult,
    MotherToD6Bridge,
    create_wire3,
    translate_pulse_to_probes,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_pulse_dict(
    sequence: int = 1,
    collective_phi: float = 0.0,
    consenting_gaians: int = 0,
    schumann_aligned_count: int = 0,
    avg_noosphere_health: float = 0.5,
    field_coherence_label: str = "dormant",
    noosphere_stage: str = "Geosphere",
) -> Dict[str, Any]:
    """Construct a minimal MotherPulse dict for testing."""
    return {
        "pulse_id": "test-pulse",
        "sequence": sequence,
        "timestamp": 1718658000.0,
        "collective_field": {
            "active_gaians": consenting_gaians,
            "consenting_gaians": consenting_gaians,
            "avg_bond_depth": 0.0,
            "avg_noosphere_health": avg_noosphere_health,
            "collective_phi": collective_phi,
            "dominant_element": "earth",
            "element_distribution": {},
            "individuation_distribution": {},
            "schumann_aligned_count": schumann_aligned_count,
            "field_coherence_label": field_coherence_label,
            "noosphere_stage": noosphere_stage,
        },
        "mother_voice": None,
        "coherence_candidate": False,
        "mesh": {"node_id": None, "peer_count": 0, "crdt_live_nodes": 0},
    }


# ---------------------------------------------------------------------------
# T01 — Dormant field maps to zero coherence
# ---------------------------------------------------------------------------

def test_T01_dormant_field_maps_to_zero_coherence():
    """
    T01: A dormant pulse (phi=0.0, no Gaians) must produce
    collective_coherence=0.0 and schumann_coherence=0.0.
    """
    pulse = _make_pulse_dict(
        sequence=1,
        collective_phi=0.0,
        consenting_gaians=0,
        schumann_aligned_count=0,
    )
    result = translate_pulse_to_probes(pulse)

    assert result.probes.collective_coherence == 0.0
    assert result.probes.schumann_coherence == 0.0
    assert result.consenting_gaians == 0
    assert result.collective_phi == 0.0


# ---------------------------------------------------------------------------
# T02 — High phi maps to high collective_coherence
# ---------------------------------------------------------------------------

def test_T02_high_phi_maps_to_high_collective_coherence():
    """
    T02: collective_phi=0.85 (high_resonance) must map to
    collective_coherence=0.85. The mapping must be direct (not inverted).
    """
    pulse = _make_pulse_dict(
        sequence=5,
        collective_phi=0.85,
        consenting_gaians=12,
        schumann_aligned_count=6,
        field_coherence_label="high_resonance",
    )
    result = translate_pulse_to_probes(pulse)

    assert result.probes.collective_coherence is not None
    assert abs(result.probes.collective_coherence - 0.85) < 0.001, (
        f"Expected collective_coherence~0.85, got {result.probes.collective_coherence}"
    )
    assert result.field_coherence_label == "high_resonance"


# ---------------------------------------------------------------------------
# T03 — Schumann ratio calculated correctly
# ---------------------------------------------------------------------------

def test_T03_schumann_ratio_calculated_correctly():
    """
    T03: With 8 consenting Gaians and 6 Schumann-aligned,
    schumann_coherence must be 0.75 (6/8).
    Zero consenting Gaians must produce schumann_coherence=0.0 (no division by zero).
    """
    # Normal case
    pulse = _make_pulse_dict(
        consenting_gaians=8,
        schumann_aligned_count=6,
    )
    result = translate_pulse_to_probes(pulse)
    assert abs(result.probes.schumann_coherence - 0.75) < 0.001, (
        f"Expected schumann_coherence=0.75, got {result.probes.schumann_coherence}"
    )

    # Zero Gaians — must not raise ZeroDivisionError
    pulse_empty = _make_pulse_dict(consenting_gaians=0, schumann_aligned_count=0)
    result_empty = translate_pulse_to_probes(pulse_empty)
    assert result_empty.probes.schumann_coherence == 0.0


# ---------------------------------------------------------------------------
# T04 — session_duration_hours derived from sequence
# ---------------------------------------------------------------------------

def test_T04_session_duration_from_pulse_sequence():
    """
    T04: session_duration_hours must equal sequence × PULSE_INTERVAL_SECONDS / 3600.
    At sequence=120 with 30s intervals → 120×30/3600 = 1.0 hour exactly.
    """
    # 120 pulses × 30s = 3600s = 1.0 hour
    sequence = int(3600 / PULSE_INTERVAL_SECONDS)
    pulse = _make_pulse_dict(sequence=sequence)
    result = translate_pulse_to_probes(pulse)

    expected_hours = 1.0
    assert abs(result.probes.session_duration_hours - expected_hours) < 0.001, (
        f"Expected session_duration_hours~1.0, got {result.probes.session_duration_hours}"
    )


# ---------------------------------------------------------------------------
# T05 — Wire 2/3 noosphere blend (60/40)
# ---------------------------------------------------------------------------

def test_T05_noosphere_blend_wire2_wire3():
    """
    T05: When wire2_noosphere_load is provided, the blended noosphere_load
    must be 60% Wire2 + 40% Wire3 (collective).

    Example:
      Wire 2 physical load: 0.80
      Wire 3 collective load: 0.20 (avg_noosphere_health=0.80 → 1-0.80=0.20)
      Expected blend: 0.60*0.80 + 0.40*0.20 = 0.48 + 0.08 = 0.56
    """
    pulse = _make_pulse_dict(avg_noosphere_health=0.80)  # collective load = 0.20
    result = translate_pulse_to_probes(pulse, wire2_noosphere_load=0.80)

    expected = round(0.60 * 0.80 + 0.40 * 0.20, 3)  # 0.56
    assert abs(result.probes.noosphere_load - expected) < 0.001, (
        f"Expected blended noosphere_load={expected}, got {result.probes.noosphere_load}"
    )


# ---------------------------------------------------------------------------
# T06 — process_pulse() returns correct types
# ---------------------------------------------------------------------------

def test_T06_process_pulse_returns_probe_result_and_event():
    """
    T06: MotherToD6Bridge.process_pulse() must return a tuple of
    (MotherProbeResult, InterventionEvent) with correct types and fields.
    """
    state = default_state()
    engine = D6Engine(auto_apply=True)
    mother = MotherThread()
    bridge = MotherToD6Bridge(mother=mother, engine=engine, state=state)

    pulse = _make_pulse_dict(
        sequence=10,
        collective_phi=0.55,
        consenting_gaians=4,
        schumann_aligned_count=3,
        avg_noosphere_health=0.75,
    )
    probe_result, event = bridge.process_pulse(pulse)

    assert isinstance(probe_result, MotherProbeResult)
    assert bridge.cycle_count == 1
    assert event is not None
    assert hasattr(event, "severity")
    assert hasattr(event, "recommended_mode")
    assert probe_result.probes.collective_coherence is not None
    assert probe_result.probes.schumann_coherence is not None


# ---------------------------------------------------------------------------
# T07 — Wire 3 → Wire 1: process_pulse fires on_intervention
# ---------------------------------------------------------------------------

def test_T07_process_pulse_fires_on_intervention_callback():
    """
    T07: Wire 3 → Wire 1 integration test.

    MotherToD6Bridge.process_pulse() must fire D6Engine's on_intervention
    callback (Wire 1). This proves:
      MotherThread pulse → Wire 3 translate → D6 evaluate → Wire 1 callback
    The full collective-field-to-HUD chain is alive.
    """
    interventions: List = []

    def capture(event):
        interventions.append(event)

    state = default_state()
    engine = D6Engine(auto_apply=True, on_intervention=capture)
    mother = MotherThread()
    bridge = MotherToD6Bridge(mother=mother, engine=engine, state=state)

    pulse = _make_pulse_dict(
        sequence=20,
        collective_phi=0.90,
        consenting_gaians=10,
        schumann_aligned_count=10,
        avg_noosphere_health=0.95,
    )
    bridge.process_pulse(pulse)

    assert len(interventions) >= 1, (
        "Wire 3 → Wire 1: process_pulse() must fire on_intervention at least once"
    )
    event = interventions[0]
    assert hasattr(event, "severity")
    assert hasattr(event, "recommended_mode")


# ---------------------------------------------------------------------------
# T08 — async run() processes live MotherThread pulses
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_T08_async_run_processes_live_pulses():
    """
    T08: MotherToD6Bridge.run() must process pulses emitted by a live
    MotherThread. We start the MotherThread, let it fire one beat,
    confirm Wire 3 processed it, then stop both.

    This is the end-to-end async integration test for Wire 3:
    live MotherThread → subscription → Wire 3 → D6 → Wire 1
    """
    interventions: List = []

    def capture(event):
        interventions.append(event)

    state = default_state()
    engine = D6Engine(auto_apply=True, on_intervention=capture)
    mother = MotherThread()

    bridge = MotherToD6Bridge(mother=mother, engine=engine, state=state)

    # Start MotherThread pulse loop
    await mother.async_start()

    # Start Wire 3 subscriber as a background task
    task = asyncio.create_task(bridge.run())

    # Force one immediate beat and broadcast
    pulse = mother._beat()
    await mother._broadcast(pulse)

    # Give Wire 3 time to process the broadcast
    await asyncio.sleep(0.05)

    # Stop both
    bridge.stop()
    task.cancel()
    mother.stop()

    # Wire 3 must have processed at least 1 pulse
    assert bridge.cycle_count >= 1, (
        f"Wire 3 async run() must process at least 1 pulse, got {bridge.cycle_count}"
    )
    # Wire 1 must have fired
    assert len(interventions) >= 1, (
        "Wire 3 → Wire 1: async run() must fire on_intervention at least once"
    )
