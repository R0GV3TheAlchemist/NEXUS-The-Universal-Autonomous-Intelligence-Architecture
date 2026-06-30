"""
GAIA System Settings — all OS-level configuration subsystems.

Modelled after the full settings spectrum required for a universal OS:
- Bluetooth & Devices
- Network & Internet
- Personalization
- Apps
- Accounts
- Time & Language
- Gaming
- Music
- Movies
- Virtual Reality
- Mixed Reality
- Accessibility
- Privacy & Security
- GAIA Update
- Display
- Sound
- Notifications
- Power & Battery
- Storage
- Multitasking
- Activation & Licensing
- Developer Mode
- Advanced System
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class BluetoothDeviceSettings:
    enabled: bool = True
    discoverable: bool = False
    paired_devices: list = field(default_factory=list)


@dataclass
class NetworkInternetSettings:
    wifi_enabled: bool = True
    ethernet_enabled: bool = True
    vpn_profiles: list = field(default_factory=list)
    proxy_config: Dict[str, Any] = field(default_factory=dict)
    hotspot_enabled: bool = False


@dataclass
class PersonalizationSettings:
    theme: str = "gaia-dark"
    accent_color: str = "#00f5d4"
    wallpaper: str = ""
    font_family: str = "Inter"
    font_size: int = 14
    animations_enabled: bool = True
    sidebar_layout: str = "left"


@dataclass
class AppsSettings:
    default_browser: str = ""
    default_media_player: str = ""
    default_email: str = ""
    startup_apps: list = field(default_factory=list)
    sideload_enabled: bool = False


@dataclass
class AccountsSettings:
    primary_account_id: str = ""
    linked_accounts: list = field(default_factory=list)
    biometric_login: bool = False
    pin_enabled: bool = True
    passkey_enabled: bool = False


@dataclass
class TimeLanguageSettings:
    timezone: str = "UTC"
    language: str = "en-US"
    region: str = "US"
    date_format: str = "YYYY-MM-DD"
    time_format_24h: bool = True
    auto_sync_time: bool = True


@dataclass
class GamingSettings:
    game_mode_enabled: bool = False
    xbox_game_bar: bool = False
    captures_folder: str = ""
    performance_overlay: bool = False


@dataclass
class MusicSettings:
    default_service: str = ""
    spatial_audio: bool = False
    equalizer_profile: str = "flat"
    crossfade_seconds: int = 0


@dataclass
class MoviesSettings:
    default_service: str = ""
    hdr_enabled: bool = True
    auto_play: bool = True
    subtitle_language: str = "en"


@dataclass
class VirtualRealitySettings:
    vr_enabled: bool = False
    headset_id: str = ""
    refresh_rate_hz: int = 90
    guardian_enabled: bool = True
    hand_tracking: bool = True


@dataclass
class MixedRealitySettings:
    mr_enabled: bool = False
    passthrough_mode: str = "color"
    hologram_opacity: float = 1.0
    spatial_anchors: list = field(default_factory=list)


@dataclass
class AccessibilitySettings:
    screen_reader: bool = False
    magnifier: bool = False
    high_contrast: bool = False
    closed_captions: bool = False
    voice_control: bool = False
    reduce_motion: bool = False
    color_blind_mode: str = "none"


@dataclass
class PrivacySecuritySettings:
    location_services: bool = True
    camera_access: bool = True
    microphone_access: bool = True
    telemetry_level: str = "minimal"
    firewall_enabled: bool = True
    secure_boot: bool = True
    tpm_enabled: bool = True
    encryption_enabled: bool = True
    zero_knowledge_mode: bool = False


@dataclass
class GAIAUpdateSettings:
    channel: str = "stable"
    auto_update: bool = True
    last_checked: str = ""
    last_installed_version: str = ""
    rollback_available: bool = False


@dataclass
class DisplaySettings:
    resolution: str = "1920x1080"
    refresh_rate_hz: int = 60
    hdr_enabled: bool = False
    night_light: bool = False
    scale_percent: int = 100
    multi_monitor_mode: str = "extend"


@dataclass
class SoundSettings:
    output_device: str = ""
    input_device: str = ""
    master_volume: int = 80
    spatial_sound: bool = False
    do_not_disturb: bool = False


@dataclass
class NotificationSettings:
    dnd_enabled: bool = False
    focus_mode: str = "off"
    app_notifications: Dict[str, bool] = field(default_factory=dict)
    banner_notifications: bool = True


@dataclass
class PowerBatterySettings:
    power_mode: str = "balanced"
    sleep_timeout_minutes: int = 15
    hibernate_enabled: bool = True
    battery_saver_threshold: int = 20


@dataclass
class StorageSettings:
    primary_drive: str = ""
    available_gb: float = 0.0
    cloud_backup_enabled: bool = False
    storage_sense_enabled: bool = True


@dataclass
class DeveloperSettings:
    dev_mode_enabled: bool = False
    ssh_server: bool = False
    usb_debugging: bool = False
    api_logging: bool = False
    experimental_features: bool = False


@dataclass
class SystemSettings:
    """Root system settings object aggregating all subsystems."""
    bluetooth: BluetoothDeviceSettings = field(default_factory=BluetoothDeviceSettings)
    network: NetworkInternetSettings = field(default_factory=NetworkInternetSettings)
    personalization: PersonalizationSettings = field(default_factory=PersonalizationSettings)
    apps: AppsSettings = field(default_factory=AppsSettings)
    accounts: AccountsSettings = field(default_factory=AccountsSettings)
    time_language: TimeLanguageSettings = field(default_factory=TimeLanguageSettings)
    gaming: GamingSettings = field(default_factory=GamingSettings)
    music: MusicSettings = field(default_factory=MusicSettings)
    movies: MoviesSettings = field(default_factory=MoviesSettings)
    virtual_reality: VirtualRealitySettings = field(default_factory=VirtualRealitySettings)
    mixed_reality: MixedRealitySettings = field(default_factory=MixedRealitySettings)
    accessibility: AccessibilitySettings = field(default_factory=AccessibilitySettings)
    privacy_security: PrivacySecuritySettings = field(default_factory=PrivacySecuritySettings)
    gaia_update: GAIAUpdateSettings = field(default_factory=GAIAUpdateSettings)
    display: DisplaySettings = field(default_factory=DisplaySettings)
    sound: SoundSettings = field(default_factory=SoundSettings)
    notifications: NotificationSettings = field(default_factory=NotificationSettings)
    power_battery: PowerBatterySettings = field(default_factory=PowerBatterySettings)
    storage: StorageSettings = field(default_factory=StorageSettings)
    developer: DeveloperSettings = field(default_factory=DeveloperSettings)

    def to_dict(self) -> dict:
        import dataclasses
        return dataclasses.asdict(self)
