"""
GAIA Release Channel Management.

Four release channels, ordered from most stable to most experimental:

  stable        — Official Release: tested, validated, production-ready.
  preview       — Release Preview: near-final builds, broad testing.
  dev           — Dev Channel: daily/weekly builds, developers and testers.
  canary        — Canary: bleeding-edge, may be unstable, experimental features.

Users opt in to a channel. GAIA Update honors the channel setting when
delivering OS, runtime, and system component updates.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReleaseChannel(str, Enum):
    STABLE = "stable"
    PREVIEW = "preview"
    DEV = "dev"
    CANARY = "canary"

    @property
    def label(self) -> str:
        return {
            ReleaseChannel.STABLE: "Official Release",
            ReleaseChannel.PREVIEW: "Release Preview",
            ReleaseChannel.DEV: "Dev Channel",
            ReleaseChannel.CANARY: "Canary",
        }[self]

    @property
    def description(self) -> str:
        return {
            ReleaseChannel.STABLE: "Fully tested, production-ready builds. Recommended for all users.",
            ReleaseChannel.PREVIEW: "Near-final builds available before official release. Broader validation.",
            ReleaseChannel.DEV: "Frequent builds for developers and advanced testers. May have rough edges.",
            ReleaseChannel.CANARY: "Bleeding-edge nightly builds. Experimental features. May be unstable.",
        }[self]

    @property
    def stability_level(self) -> int:
        """Higher = more stable."""
        return {ReleaseChannel.STABLE: 4, ReleaseChannel.PREVIEW: 3, ReleaseChannel.DEV: 2, ReleaseChannel.CANARY: 1}[self]


@dataclass
class ReleaseVersion:
    channel: ReleaseChannel
    version: str
    build_id: str
    release_notes: str = ""
    released_at: str = field(default_factory=_utcnow)
    mandatory: bool = False
    rollback_version: Optional[str] = None


@dataclass
class ReleaseChannelManager:
    current_channel: ReleaseChannel = ReleaseChannel.STABLE
    installed_version: str = "0.1.0"
    available_versions: List[ReleaseVersion] = field(default_factory=list)

    def switch_channel(self, channel: ReleaseChannel) -> None:
        self.current_channel = channel

    def register_release(self, release: ReleaseVersion) -> None:
        self.available_versions.append(release)

    def latest_for_channel(self, channel: ReleaseChannel) -> Optional[ReleaseVersion]:
        matching = [r for r in self.available_versions if r.channel == channel]
        return matching[-1] if matching else None

    def check_for_update(self) -> Optional[ReleaseVersion]:
        return self.latest_for_channel(self.current_channel)

    def all_channels(self) -> List[dict]:
        return [
            {
                "channel": ch.value,
                "label": ch.label,
                "description": ch.description,
                "stability": ch.stability_level,
            }
            for ch in ReleaseChannel
        ]
