"""Unit tests: Shadow Registry — Canon C23."""

import pytest
from core.memory.shadow_registry import ShadowRegistry, ShadowPattern


@pytest.fixture
def registry():
    return ShadowRegistry("gaian-001", "hp-001")


class TestShadowRegistry:
    def test_log_creates_entry(self, registry):
        entry = registry.log(
            pattern=ShadowPattern.CYCLING,
            session_id="s1",
            description="Returned to unresolved grief loop",
        )
        assert entry.pattern == ShadowPattern.CYCLING
        assert registry.count() == 1

    def test_resolve_entry(self, registry):
        entry = registry.log(ShadowPattern.AVOIDANCE, "s1", "Avoided financial discussion")
        registry.resolve_entry(entry.id, what_helped="Gentle naming")
        assert entry.is_resolved
        assert registry.count(unresolved_only=True) == 0

    def test_active_flags_returns_unresolved_patterns(self, registry):
        registry.log(ShadowPattern.CYCLING, "s1", "loop")
        registry.log(ShadowPattern.AVOIDANCE, "s1", "avoiding")
        flags = registry.active_flags()
        assert ShadowPattern.CYCLING in flags
        assert ShadowPattern.AVOIDANCE in flags

    def test_pattern_frequency(self, registry):
        registry.log(ShadowPattern.CYCLING, "s1", "a")
        registry.log(ShadowPattern.CYCLING, "s2", "b")
        registry.log(ShadowPattern.AVOIDANCE, "s1", "c")
        freq = registry.pattern_frequency()
        assert freq[ShadowPattern.CYCLING.value] == 2
        assert freq[ShadowPattern.AVOIDANCE.value] == 1

    def test_by_session(self, registry):
        registry.log(ShadowPattern.CYCLING, "s1", "in s1")
        registry.log(ShadowPattern.AVOIDANCE, "s2", "in s2")
        assert len(registry.by_session("s1")) == 1
        assert len(registry.by_session("s2")) == 1
