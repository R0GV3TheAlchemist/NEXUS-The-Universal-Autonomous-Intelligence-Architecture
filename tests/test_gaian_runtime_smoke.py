"""
tests/test_gaian_runtime_smoke.py
Smoke tests for the full GAIANRuntime chain — v1.2.0 (twelve engines).

These tests verify that the entire engine chain fires without error
and that every output contract is satisfied. They do not test the
detailed logic of individual engines (covered in unit test files).

Strategy:
  - Use a temporary in-memory directory for GAIAN state
  - Run process() with a variety of message types
  - Assert every field of RuntimeResult is present and typed correctly
  - Assert system prompt contains all expected blocks
  - Assert state snapshot contains all twelve engine keys
  - Assert SynergyReading is present and valid
  - Assert VitalityState is persisted and accessible  [T-VITA]
"""
import pytest
import json
import tempfile
import os
from core.gaian_runtime import GAIANRuntime, RuntimeResult, GAIANIdentity


@pytest.fixture
def tmp_runtime(tmp_path):
    return GAIANRuntime(
        gaian_name="TestGAIAN",
        memory_dir=str(tmp_path),
        identity=GAIANIdentity(
            name="TestGAIAN",
            pronouns="they/them",
            archetype="The Test Mirror",
            voice_base="clear, precise",
            platform="test",
        ),
    )


SAMPLE_MESSAGES = [
    "Hello, I just wanted to check in today.",
    "I've been feeling really disconnected from everything lately.",
    "I had a breakthrough moment in meditation this morning.",
    "I'm angry and I don't know why.",
    "I feel at peace. Genuinely settled.",
]


class TestRuntimeResultContract:
    def test_process_returns_runtime_result(self, tmp_runtime):
        result = tmp_runtime.process("Hello.")
        assert isinstance(result, RuntimeResult)

    def test_system_prompt_is_nonempty_string(self, tmp_runtime):
        result = tmp_runtime.process("Hello.")
        assert isinstance(result.system_prompt, str)
        assert len(result.system_prompt) > 100

    def test_system_prompt_contains_constitutional_floor(self, tmp_runtime):
        result = tmp_runtime.process("Hello.")
        assert "GAIA CONSTITUTIONAL FLOOR" in result.system_prompt

    def test_system_prompt_contains_identity_block(self, tmp_runtime):
        result = tmp_runtime.process("Hello.")
        assert "GAIAN IDENTITY" in result.system_prompt

    def test_system_prompt_contains_engine_state_block(self, tmp_runtime):
        result = tmp_runtime.process("Hello.")
        assert "LIVE ENGINE STATE" in result.system_prompt

    def test_system_prompt_contains_synergy_block(self, tmp_runtime):
        result = tmp_runtime.process("Hello.")
        assert "ELEMENTAL SYNERGY" in result.system_prompt
        assert "Synergy Factor" in result.system_prompt

    def test_synergy_reading_present(self, tmp_runtime):
        from core.synergy_engine import SynergyReading
        result = tmp_runtime.process("Hello.")
        assert isinstance(result.synergy, SynergyReading)

    def test_synergy_factor_in_bounds(self, tmp_runtime):
        result = tmp_runtime.process("Hello.")
        assert 0.0 <= result.synergy.synergy_factor <= 1.0

    def test_state_snapshot_has_all_engine_keys(self, tmp_runtime):
        """v1.2.0: snapshot must include 'vitality' key from T-VITA."""
        result = tmp_runtime.process("Hello.")
        expected_keys = [
            "gaian", "layer", "neuro", "attachment", "settling",
            "feeling", "love_arc", "meta_coherence", "codex_stage",
            "soul_mirror", "resonance_field", "synergy",
            "vitality",                                            # T-VITA
            "codex_tier", "noosphere_health",
        ]
        for key in expected_keys:
            assert key in result.state_snapshot, f"Missing key in snapshot: {key}"

    def test_synergy_snapshot_has_required_fields(self, tmp_runtime):
        result = tmp_runtime.process("Hello.")
        sy = result.state_snapshot["synergy"]
        for key in ["synergy_factor", "dominant_stage", "dominant_friction",
                    "is_low_synergy", "is_high_synergy", "dimensions"]:
            assert key in sy

    def test_vitality_summary_present_in_result(self, tmp_runtime):  # T-VITA
        """RuntimeResult.vitality_summary must be a dict after process()."""
        result = tmp_runtime.process("Hello.")
        assert isinstance(result.vitality_summary, dict)


class TestRuntimeMultipleTurns:
    def test_multiple_messages_do_not_raise(self, tmp_runtime):
        for msg in SAMPLE_MESSAGES:
            result = tmp_runtime.process(msg)
            assert isinstance(result, RuntimeResult)

    def test_bond_depth_is_nonnegative(self, tmp_runtime):
        for msg in SAMPLE_MESSAGES:
            result = tmp_runtime.process(msg)
            assert result.attachment.bond_depth >= 0.0

    def test_synergy_factor_always_in_bounds(self, tmp_runtime):
        for msg in SAMPLE_MESSAGES:
            result = tmp_runtime.process(msg)
            assert 0.0 <= result.synergy.synergy_factor <= 1.0

    def test_turn_history_grows_with_turns(self, tmp_runtime):
        for i, msg in enumerate(SAMPLE_MESSAGES, 1):
            tmp_runtime.process(msg)
        assert len(tmp_runtime.synergy_state.turn_history) == len(SAMPLE_MESSAGES)

    def test_vitality_total_turns_increments(self, tmp_runtime):     # T-VITA
        """VitalityState.total_turns must increment with each process() call."""
        for msg in SAMPLE_MESSAGES:
            tmp_runtime.process(msg)
        assert tmp_runtime.vitality_state.total_turns == len(SAMPLE_MESSAGES)


class TestRuntimePersistence:
    def test_memory_file_created_after_process(self, tmp_path):
        rt = GAIANRuntime(gaian_name="PersistTest", memory_dir=str(tmp_path))
        rt.process("Hello.")
        mem_file = tmp_path / "PersistTest" / "memory.json"
        assert mem_file.exists()

    def test_memory_contains_synergy_key(self, tmp_path):
        rt = GAIANRuntime(gaian_name="PersistTest", memory_dir=str(tmp_path))
        rt.process("Hello.")
        mem_file = tmp_path / "PersistTest" / "memory.json"
        memory = json.loads(mem_file.read_text())
        assert "synergy" in memory
        assert "last_factor" in memory["synergy"]

    def test_memory_contains_vitality_key(self, tmp_path):           # T-VITA
        """VitalityState must be persisted in memory.json after process()."""
        rt = GAIANRuntime(gaian_name="VitaTest", memory_dir=str(tmp_path))
        rt.process("Hello.")
        mem_file = tmp_path / "VitaTest" / "memory.json"
        memory = json.loads(mem_file.read_text())
        assert "vitality" in memory
        assert "total_turns" in memory["vitality"]
        assert "dose_history" in memory["vitality"]

    def test_schema_version_is_1_9(self, tmp_path):                  # T-VITA: bumped 1.8 → 1.9
        """Schema version must match MEMORY_SCHEMA_VERSION = '1.9'."""
        rt = GAIANRuntime(gaian_name="SchemaTest", memory_dir=str(tmp_path))
        rt.process("Hello.")
        mem_file = tmp_path / "SchemaTest" / "memory.json"
        memory = json.loads(mem_file.read_text())
        assert memory["schema_version"] == "1.9"


class TestGetStatus:
    def test_get_status_returns_dict(self, tmp_runtime):
        assert isinstance(tmp_runtime.get_status(), dict)

    def test_get_status_contains_synergy(self, tmp_runtime):
        status = tmp_runtime.get_status()
        assert "synergy" in status
        assert "last_factor" in status["synergy"]

    def test_get_status_contains_vitality(self, tmp_runtime):        # T-VITA
        """get_status() must include vitality health summary."""
        status = tmp_runtime.get_status()
        assert "vitality" in status

    def test_get_vitality_status_returns_dict(self, tmp_runtime):    # T-VITA
        """get_vitality_status() public accessor must return a dict."""
        assert isinstance(tmp_runtime.get_vitality_status(), dict)
