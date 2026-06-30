"""Domain types for GAIA Connectors."""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class ConnectorKind(str, Enum):
    # External services
    CALENDAR = "calendar"
    COMMUNICATIONS = "communications"
    EMAIL = "email"
    STORAGE = "storage"
    DATABASE = "database"
    # Hardware / OS
    OS_INTERFACE = "os_interface"
    BLUETOOTH = "bluetooth"
    NETWORK = "network"
    IOT = "iot"
    HARDWARE_BUS = "hardware_bus"
    # Media & Environment
    AUDIO = "audio"
    VIDEO = "video"
    DISPLAY = "display"
    MIXED_REALITY = "mixed_reality"
    # Data streams
    STREAMING = "streaming"
    WEBHOOK = "webhook"
    REST_API = "rest_api"
    GRAPHQL = "graphql"
    GRPC = "grpc"
    # Identity & Security
    IDENTITY_PROVIDER = "identity_provider"
    SECRETS_VAULT = "secrets_vault"
    # AI/ML
    LLM_PROVIDER = "llm_provider"
    EMBEDDING = "embedding"
    VISION = "vision"
    SPEECH = "speech"
    # Custom
    CUSTOM = "custom"


class ConnectorStatus(str, Enum):
    REGISTERED = "registered"
    CONNECTED = "connected"
    DEGRADED = "degraded"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class ConnectorManifest:
    """Static descriptor registered at connector boot time."""
    connector_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    kind: ConnectorKind = ConnectorKind.CUSTOM
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    capabilities: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    requires_auth: bool = False
    platform_tags: List[str] = field(default_factory=list)
    registered_at: str = field(default_factory=_utcnow)


@dataclass
class ConnectorEvent:
    """Event emitted by a connector to the GAIA event bus."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    connector_id: str = ""
    event_type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = ""
    occurred_at: str = field(default_factory=_utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
