"""
GAIA HAL Registry — the single source of truth for all devices GAIA knows.

The HALRegistry is a pure data store: it registers, indexes, and retrieves
devices. It has no authority to grant capabilities — that belongs to the
DeviceManager. This separation ensures the registry can be introspected
safely without any risk of privilege escalation through lookup.

Design principle (seL4-inspired): knowing a device exists is not the same
as being authorised to access it. The registry answers "what is here";
the Device Manager answers "who may touch it".
"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional

from core.os_interface.device.model import (
    DeviceKind,
    DeviceState,
    GAIADevice,
    HotplugEvent,
)


HotplugListener = Callable[[HotplugEvent], None]


class HALRegistry:
    """
    Runtime device registry with hotplug event dispatch.

    Devices are indexed by device_id (primary) and by kind (secondary).
    Hotplug listeners are called synchronously on registration, removal,
    and state transitions — they form the foundation of GAIA's device
    event bus.
    """

    def __init__(self) -> None:
        self._devices: Dict[str, GAIADevice] = {}
        self._kind_index: Dict[DeviceKind, List[str]] = {}
        self._listeners: List[HotplugListener] = []

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, device: GAIADevice) -> GAIADevice:
        """Register a device and fire a ATTACHED hotplug event."""
        self._devices[device.device_id] = device
        self._kind_index.setdefault(device.kind, []).append(device.device_id)
        device.transition(DeviceState.READY if device.state == DeviceState.DETECTED else device.state)
        self._emit(HotplugEvent(
            action=__import__('core.os_interface.device.model', fromlist=['HotplugAction']).HotplugAction.ATTACHED,
            device_id=device.device_id,
            device_kind=device.kind,
            device_name=device.name,
            new_state=device.state,
        ))
        return device

    def deregister(self, device_id: str) -> Optional[GAIADevice]:
        """Remove a device (hotplug removal) and fire a DETACHED event."""
        device = self._devices.pop(device_id, None)
        if device is None:
            return None
        kind_list = self._kind_index.get(device.kind, [])
        if device_id in kind_list:
            kind_list.remove(device_id)
        device.transition(DeviceState.REMOVED)
        self._emit(HotplugEvent(
            action=__import__('core.os_interface.device.model', fromlist=['HotplugAction']).HotplugAction.DETACHED,
            device_id=device_id,
            device_kind=device.kind,
            device_name=device.name,
            new_state=DeviceState.REMOVED,
        ))
        return device

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, device_id: str) -> Optional[GAIADevice]:
        return self._devices.get(device_id)

    def require(self, device_id: str) -> GAIADevice:
        d = self.get(device_id)
        if d is None:
            raise KeyError(f"Device '{device_id}' is not registered in the HAL Registry.")
        return d

    def by_kind(self, kind: DeviceKind) -> List[GAIADevice]:
        ids = self._kind_index.get(kind, [])
        return [self._devices[i] for i in ids if i in self._devices]

    def all_devices(self) -> List[GAIADevice]:
        return list(self._devices.values())

    def accessible(self) -> List[GAIADevice]:
        return [d for d in self._devices.values() if d.is_accessible()]

    def count(self) -> int:
        return len(self._devices)

    # ------------------------------------------------------------------
    # Hotplug event bus
    # ------------------------------------------------------------------

    def add_listener(self, listener: HotplugListener) -> None:
        self._listeners.append(listener)

    def remove_listener(self, listener: HotplugListener) -> None:
        self._listeners = [l for l in self._listeners if l is not listener]

    def _emit(self, event: HotplugEvent) -> None:
        for listener in self._listeners:
            try:
                listener(event)
            except Exception:
                pass  # listeners must not crash the registry

    # ------------------------------------------------------------------
    # Device tree snapshot
    # ------------------------------------------------------------------

    def device_tree(self) -> Dict[str, list]:
        """Return a kind-grouped snapshot of all registered devices."""
        tree: Dict[str, list] = {}
        for kind, ids in self._kind_index.items():
            devices = [self._devices[i].summary() for i in ids if i in self._devices]
            if devices:
                tree[kind.value] = devices
        return tree
