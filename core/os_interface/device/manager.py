"""
GAIA Device Manager — authority over device access and capability issuance.

The Device Manager is the *only* entity that may issue DeviceCapabilityTokens.
It sits above the HALRegistry (which only stores devices) and enforces the
capability security model: no process touches hardware without a token,
and every token can be revoked at any time.

This mirrors DriverKit's user-space driver authority model (XNU) combined
with seL4's capability derivation rules: the manager holds the "master
capability" to each device and derives bounded sub-capabilities for callers.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.os_interface.device.model import (
    DeviceCapabilityToken,
    DeviceKind,
    DevicePowerState,
    DeviceState,
    GAIADevice,
    HotplugEvent,
)
from core.os_interface.device.registry import HALRegistry


class DeviceAccessError(Exception):
    pass


class DeviceManager:
    """
    The runtime authority for device access in GAIA.

    Responsibilities:
      1. Own the HALRegistry — register/deregister devices
      2. Issue DeviceCapabilityTokens to authorized processes
      3. Revoke tokens (individually or all tokens for a device/process)
      4. Bind driver processes to devices
      5. Manage device power state transitions
      6. Provide device queries to the Process Manager and Session layer
    """

    KERNEL_PID = "kernel"

    def __init__(self) -> None:
        self.registry = HALRegistry()
        self._tokens: Dict[str, DeviceCapabilityToken] = {}
        # Index: device_id -> list of token_ids
        self._device_tokens: Dict[str, List[str]] = {}
        # Index: pid -> list of token_ids
        self._process_tokens: Dict[str, List[str]] = {}

    # ------------------------------------------------------------------
    # Device Registration (open registration — anything can be added)
    # ------------------------------------------------------------------

    def register_device(
        self,
        name: str,
        kind: DeviceKind,
        vendor: str = "",
        model: str = "",
        firmware_version: str = "",
        bus_path: str = "",
        capabilities: Optional[List[str]] = None,
        properties: Optional[Dict[str, Any]] = None,
        virtual: bool = False,
    ) -> GAIADevice:
        """Register any device — physical, virtual, emulated, or future."""
        device = GAIADevice(
            name=name,
            kind=kind,
            vendor=vendor,
            model=model,
            firmware_version=firmware_version,
            bus_path=bus_path,
            capabilities=capabilities or [],
            properties=properties or {},
            state=DeviceState.VIRTUAL if virtual else DeviceState.DETECTED,
        )
        self.registry.register(device)
        return device

    def deregister_device(self, device_id: str) -> Optional[GAIADevice]:
        """Remove a device and revoke all outstanding tokens for it."""
        self.revoke_all_tokens_for_device(device_id)
        return self.registry.deregister(device_id)

    # ------------------------------------------------------------------
    # Driver Binding
    # ------------------------------------------------------------------

    def bind_driver(self, device_id: str, driver_pid: str) -> None:
        """Assign a driver process as the exclusive service provider for a device."""
        device = self.registry.require(device_id)
        device.driver_pid = driver_pid
        device.transition(DeviceState.READY)

    def unbind_driver(self, device_id: str) -> None:
        device = self.registry.require(device_id)
        device.driver_pid = None
        device.transition(DeviceState.DETECTED)

    # ------------------------------------------------------------------
    # Capability Token Issuance
    # ------------------------------------------------------------------

    def issue_token(
        self,
        device_id: str,
        holder_pid: str,
        read: bool = True,
        write: bool = False,
        exclusive: bool = False,
        delegate: bool = False,
        issued_by: str = KERNEL_PID,
        expires_at: Optional[str] = None,
    ) -> DeviceCapabilityToken:
        """
        Issue a capability token granting a process access to a device.

        Exclusive tokens are rejected if another exclusive token is already
        active for the same device — enforcing hardware mutual exclusion.
        """
        device = self.registry.require(device_id)
        if not device.is_accessible():
            raise DeviceAccessError(
                f"Device '{device.name}' is not accessible (state={device.state.value})."
            )
        if exclusive:
            active_exclusive = [
                self._tokens[tid]
                for tid in self._device_tokens.get(device_id, [])
                if tid in self._tokens
                and self._tokens[tid].is_active()
                and self._tokens[tid].exclusive
            ]
            if active_exclusive:
                raise DeviceAccessError(
                    f"Device '{device.name}' already has an exclusive token held by "
                    f"PID '{active_exclusive[0].holder_pid}'."
                )
        token = DeviceCapabilityToken(
            device_id=device_id,
            holder_pid=holder_pid,
            read=read,
            write=write,
            exclusive=exclusive,
            delegate=delegate,
            issued_by=issued_by,
            expires_at=expires_at,
        )
        self._tokens[token.token_id] = token
        self._device_tokens.setdefault(device_id, []).append(token.token_id)
        self._process_tokens.setdefault(holder_pid, []).append(token.token_id)
        return token

    def revoke_token(self, token_id: str) -> bool:
        token = self._tokens.get(token_id)
        if token is None:
            return False
        token.revoked = True
        return True

    def revoke_all_tokens_for_device(self, device_id: str) -> int:
        """Revoke every active token for a device (e.g. on removal)."""
        count = 0
        for tid in self._device_tokens.get(device_id, []):
            if self.revoke_token(tid):
                count += 1
        return count

    def revoke_all_tokens_for_process(self, pid: str) -> int:
        """Revoke all device tokens held by a process (e.g. on process exit)."""
        count = 0
        for tid in self._process_tokens.get(pid, []):
            if self.revoke_token(tid):
                count += 1
        return count

    # ------------------------------------------------------------------
    # Token Verification
    # ------------------------------------------------------------------

    def verify_token(
        self,
        token_id: str,
        holder_pid: str,
        require_write: bool = False,
    ) -> DeviceCapabilityToken:
        """Verify a token is active, held by the right process, and has required rights."""
        token = self._tokens.get(token_id)
        if token is None:
            raise DeviceAccessError(f"Token '{token_id}' does not exist.")
        if token.revoked:
            raise DeviceAccessError(f"Token '{token_id}' has been revoked.")
        if token.holder_pid != holder_pid:
            raise DeviceAccessError(
                f"Token '{token_id}' is held by PID '{token.holder_pid}', not '{holder_pid}'."
            )
        if require_write and not token.write:
            raise DeviceAccessError(f"Token '{token_id}' does not grant write access.")
        return token

    # ------------------------------------------------------------------
    # Power Management
    # ------------------------------------------------------------------

    def set_power_state(self, device_id: str, power_state: DevicePowerState) -> None:
        self.registry.require(device_id).power_transition(power_state)

    def suspend_all(self, kind: Optional[DeviceKind] = None) -> int:
        """Suspend all (or all-of-kind) accessible devices. Returns count."""
        targets = self.registry.by_kind(kind) if kind else self.registry.accessible()
        for device in targets:
            device.power_transition(DevicePowerState.SLEEP)
        return len(targets)

    def resume_all(self, kind: Optional[DeviceKind] = None) -> int:
        targets = self.registry.by_kind(kind) if kind else self.registry.all_devices()
        resumed = 0
        for device in targets:
            if device.power_state in (DevicePowerState.SLEEP, DevicePowerState.IDLE):
                device.power_transition(DevicePowerState.ACTIVE)
                resumed += 1
        return resumed

    # ------------------------------------------------------------------
    # Query API (for Process Manager, Session layer, GKE hooks)
    # ------------------------------------------------------------------

    def tokens_for_process(self, pid: str) -> List[DeviceCapabilityToken]:
        return [
            self._tokens[tid]
            for tid in self._process_tokens.get(pid, [])
            if tid in self._tokens and self._tokens[tid].is_active()
        ]

    def tokens_for_device(self, device_id: str) -> List[DeviceCapabilityToken]:
        return [
            self._tokens[tid]
            for tid in self._device_tokens.get(device_id, [])
            if tid in self._tokens and self._tokens[tid].is_active()
        ]

    def process_table(self) -> List[Dict[str, Any]]:
        return self.registry.device_tree()

    def on_hotplug(self, listener) -> None:
        self.registry.add_listener(listener)
