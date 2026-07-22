"""tests/test_sovereignmemory.py

Test scaffold for src-python/sovereignmemory

Covers: SovereignMemory, memory_router, init_memory
"""
import pytest

sovereignmemory = pytest.importorskip("sovereignmemory")


class TestSovereignMemory:

    @pytest.mark.xfail(reason="Not yet implemented (Phase B stub)")
    def test_init_memory_returns_instance(self):
        from sovereignmemory import init_memory
        mem = init_memory()
        assert mem is not None

    @pytest.mark.xfail(reason="Not yet implemented (Phase B stub)")
    def test_store_and_retrieve(self):
        from sovereignmemory import SovereignMemory
        mem = SovereignMemory()
        mem.store(key="test-key", value={"data": 42})
        result = mem.retrieve("test-key")
        assert result["data"] == 42

    @pytest.mark.xfail(reason="Not yet implemented (Phase B stub)")
    def test_consent_gate_blocks_unauthorised_read(self):
        from sovereignmemory import SovereignMemory
        mem = SovereignMemory()
        mem.store(key="private", value="secret", restricted=True)
        with pytest.raises(PermissionError):
            mem.retrieve("private", caller="unknown-agent")
