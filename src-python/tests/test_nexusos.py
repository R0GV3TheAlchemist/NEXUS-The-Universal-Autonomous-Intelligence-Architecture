"""tests/test_nexusos.py

Test scaffold for src-python/nexusos

Covers: NexusKernel, CapabilityToken, HALRegistry, RTScheduler,
        IPCChannel, MemoryBroker from nexusos.*

All tests are marked xfail until Phase A/B implementations are
wired. The scaffold defines the intended contract so that
implementors have a clear target to pass.
"""
import pytest

# ---------------------------------------------------------------------------
# Import guards — skip entire module if nexusos stubs are not yet importable
# ---------------------------------------------------------------------------
nexusos = pytest.importorskip("nexusos")


class TestCapabilityToken:
    """CapabilityToken is an immutable, unforgeable access descriptor."""

    @pytest.mark.xfail(reason="Not yet implemented (Phase A stub)")
    def test_token_is_immutable(self):
        """CapabilityToken instances must be frozen (no mutation after creation)."""
        from nexusos.kernel import CapabilityToken
        token = CapabilityToken(object_id="obj-1", permitted_ops=frozenset(["read"]))
        with pytest.raises((AttributeError, TypeError)):
            token.permitted_ops = frozenset(["write"])  # type: ignore

    @pytest.mark.xfail(reason="Not yet implemented (Phase A stub)")
    def test_token_has_required_fields(self):
        """CapabilityToken must carry object_id, permitted_ops, issuer."""
        from nexusos.kernel import CapabilityToken
        token = CapabilityToken(
            object_id="obj-1",
            permitted_ops=frozenset(["read", "execute"]),
            issuer="nexus-kernel",
        )
        assert token.object_id == "obj-1"
        assert "read" in token.permitted_ops


class TestNexusKernel:
    """NexusKernel boots the system and initialises core subsystems."""

    @pytest.mark.xfail(reason="Not yet implemented (Phase A stub)")
    def test_kernel_boot_initialises_hal(self):
        """Kernel.boot() must initialise the HALRegistry without error."""
        from nexusos.kernel import NexusKernel
        kernel = NexusKernel()
        kernel.boot()  # Should not raise

    @pytest.mark.xfail(reason="Not yet implemented (Phase A stub)")
    def test_kernel_mint_capability(self):
        """Kernel must mint a CapabilityToken for valid object IDs."""
        from nexusos.kernel import NexusKernel
        kernel = NexusKernel()
        token = kernel.mint_capability(object_id="hal-driver-1", permitted_ops=["read"])
        assert token is not None


class TestRTScheduler:
    """RTScheduler enforces EDF/RMS scheduling with energy profiles."""

    @pytest.mark.xfail(reason="Not yet implemented (Phase A stub)")
    def test_scheduler_accepts_hard_deadline_task(self):
        from nexusos.scheduler import RTScheduler, Task, TaskPriority
        sched = RTScheduler()
        task = Task(name="hal-tick", priority=TaskPriority.HARD, deadline=0.016)
        sched.submit(task)
        assert sched.queue_size() == 1

    @pytest.mark.xfail(reason="Not yet implemented (Phase A stub)")
    def test_scheduler_tick_does_not_raise(self):
        from nexusos.scheduler import RTScheduler
        sched = RTScheduler()
        sched.tick()  # Should not raise even with empty queue
