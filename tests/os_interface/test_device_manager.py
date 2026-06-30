from __future__ import annotations

import pytest

from core.os_interface.device.manager import DeviceAccessError, DeviceManager
from core.os_interface.device.model import (
    DeviceKind,
    DevicePowerState,
    DeviceState,
    HotplugAction,
)


class TestDeviceRegistration:
    def test_register_physical_device(self):
        mgr = DeviceManager()
        device = mgr.register_device("Apple M3 CPU", DeviceKind.CPU, vendor="Apple", model="M3")
        assert device.state == DeviceState.READY
        assert mgr.registry.get(device.device_id) is not None

    def test_register_virtual_device(self):
        mgr = DeviceManager()
        device = mgr.register_device("GAIA Loopback", DeviceKind.LOOPBACK, virtual=True)
        assert device.state == DeviceState.VIRTUAL
        assert device.is_accessible()

    def test_register_neural_engine(self):
        mgr = DeviceManager()
        device = mgr.register_device(
            "Apple Neural Engine", DeviceKind.NEURAL_ENGINE,
            vendor="Apple", model="ANE-M3",
            capabilities=["matrix_multiply", "convolution", "attention"]
        )
        assert device.kind == DeviceKind.NEURAL_ENGINE
        assert "attention" in device.capabilities

    def test_register_anything_open_registration(self):
        """Any DeviceKind can be registered — open registration principle."""
        mgr = DeviceManager()
        for kind in DeviceKind:
            d = mgr.register_device(f"test-{kind.value}", kind, virtual=True)
            assert d.is_accessible()

    def test_deregister_device(self):
        mgr = DeviceManager()
        device = mgr.register_device("USB Drive", DeviceKind.REMOVABLE_STORAGE)
        mgr.deregister_device(device.device_id)
        assert mgr.registry.get(device.device_id) is None

    def test_deregister_revokes_all_tokens(self):
        mgr = DeviceManager()
        device = mgr.register_device("GPU", DeviceKind.GPU)
        token = mgr.issue_token(device.device_id, "pid-a", write=True)
        assert token.is_active()
        mgr.deregister_device(device.device_id)
        assert not token.is_active()


class TestDriverBinding:
    def test_bind_driver(self):
        mgr = DeviceManager()
        device = mgr.register_device("NVMe SSD", DeviceKind.STORAGE)
        mgr.bind_driver(device.device_id, "driver-pid-nvme")
        assert device.driver_pid == "driver-pid-nvme"
        assert device.state == DeviceState.READY

    def test_unbind_driver(self):
        mgr = DeviceManager()
        device = mgr.register_device("NVMe SSD", DeviceKind.STORAGE)
        mgr.bind_driver(device.device_id, "driver-pid-nvme")
        mgr.unbind_driver(device.device_id)
        assert device.driver_pid is None


class TestCapabilityTokens:
    def test_issue_token(self):
        mgr = DeviceManager()
        device = mgr.register_device("Display", DeviceKind.DISPLAY)
        token = mgr.issue_token(device.device_id, "pid-ui", write=True)
        assert token.is_active()
        assert token.holder_pid == "pid-ui"
        assert token.write

    def test_verify_token(self):
        mgr = DeviceManager()
        device = mgr.register_device("Microphone", DeviceKind.MICROPHONE)
        token = mgr.issue_token(device.device_id, "pid-voice")
        verified = mgr.verify_token(token.token_id, "pid-voice")
        assert verified.token_id == token.token_id

    def test_verify_token_wrong_pid_raises(self):
        mgr = DeviceManager()
        device = mgr.register_device("Camera", DeviceKind.CAMERA)
        token = mgr.issue_token(device.device_id, "pid-a")
        with pytest.raises(DeviceAccessError):
            mgr.verify_token(token.token_id, "pid-b")

    def test_revoke_token(self):
        mgr = DeviceManager()
        device = mgr.register_device("GPU", DeviceKind.GPU)
        token = mgr.issue_token(device.device_id, "pid-render")
        mgr.revoke_token(token.token_id)
        with pytest.raises(DeviceAccessError):
            mgr.verify_token(token.token_id, "pid-render")

    def test_exclusive_token_blocks_second_exclusive(self):
        mgr = DeviceManager()
        device = mgr.register_device("Quantum CPU", DeviceKind.QUANTUM_PROCESSOR)
        mgr.issue_token(device.device_id, "pid-a", exclusive=True)
        with pytest.raises(DeviceAccessError):
            mgr.issue_token(device.device_id, "pid-b", exclusive=True)

    def test_non_exclusive_tokens_stack(self):
        mgr = DeviceManager()
        device = mgr.register_device("Audio", DeviceKind.AUDIO_OUTPUT)
        t1 = mgr.issue_token(device.device_id, "pid-music")
        t2 = mgr.issue_token(device.device_id, "pid-notify")
        assert t1.is_active()
        assert t2.is_active()

    def test_revoke_all_tokens_for_process(self):
        mgr = DeviceManager()
        d1 = mgr.register_device("Display", DeviceKind.DISPLAY)
        d2 = mgr.register_device("Audio", DeviceKind.AUDIO_OUTPUT)
        t1 = mgr.issue_token(d1.device_id, "pid-app")
        t2 = mgr.issue_token(d2.device_id, "pid-app")
        count = mgr.revoke_all_tokens_for_process("pid-app")
        assert count == 2
        assert not t1.is_active()
        assert not t2.is_active()

    def test_inaccessible_device_raises_on_issue(self):
        mgr = DeviceManager()
        device = mgr.register_device("Faulted GPU", DeviceKind.GPU)
        device.transition(DeviceState.FAULTED)
        with pytest.raises(DeviceAccessError):
            mgr.issue_token(device.device_id, "pid-a")


class TestPowerManagement:
    def test_suspend_all(self):
        mgr = DeviceManager()
        mgr.register_device("Display", DeviceKind.DISPLAY)
        mgr.register_device("Audio", DeviceKind.AUDIO_OUTPUT)
        count = mgr.suspend_all()
        assert count == 2
        for d in mgr.registry.all_devices():
            assert d.power_state == DevicePowerState.SLEEP

    def test_resume_all(self):
        mgr = DeviceManager()
        mgr.register_device("Display", DeviceKind.DISPLAY)
        mgr.suspend_all()
        count = mgr.resume_all()
        assert count == 1

    def test_suspend_by_kind(self):
        mgr = DeviceManager()
        mgr.register_device("Display", DeviceKind.DISPLAY)
        mgr.register_device("Audio", DeviceKind.AUDIO_OUTPUT)
        count = mgr.suspend_all(kind=DeviceKind.DISPLAY)
        assert count == 1


class TestHotplugEvents:
    def test_hotplug_attach_fires_listener(self):
        mgr = DeviceManager()
        events = []
        mgr.on_hotplug(events.append)
        mgr.register_device("USB Drive", DeviceKind.REMOVABLE_STORAGE)
        assert len(events) == 1
        assert events[0].action == HotplugAction.ATTACHED

    def test_hotplug_detach_fires_listener(self):
        mgr = DeviceManager()
        events = []
        mgr.on_hotplug(events.append)
        device = mgr.register_device("USB Drive", DeviceKind.REMOVABLE_STORAGE)
        mgr.deregister_device(device.device_id)
        assert events[1].action == HotplugAction.DETACHED

    def test_device_tree_groups_by_kind(self):
        mgr = DeviceManager()
        mgr.register_device("CPU-0", DeviceKind.CPU)
        mgr.register_device("CPU-1", DeviceKind.CPU)
        mgr.register_device("Display-0", DeviceKind.DISPLAY)
        tree = mgr.process_table()
        assert len(tree[DeviceKind.CPU.value]) == 2
        assert len(tree[DeviceKind.DISPLAY.value]) == 1
