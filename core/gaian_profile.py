# Copyright © 2025–2026 Kyle Alexander Steen. All rights reserved. AGPL-3.0.
"""
GAIANProfile — Adaptive Per-Person Console & Personalization Layer

The missing connective tissue between GaianBirth → AkashicEngine → GAIANRuntime.
Without this layer, the console cannot adapt. Without adaptation, it is not a
GAIAN console — it is a generic UI.

Related: Issue #756 (Phase 1 — Types & Storage)
Python-side model. TypeScript types live in src/gaian/GAIANProfile.ts (to be created).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class LCITrend(str, Enum):
    ASCENDING = "ascending"
    STABLE = "stable"
    DESCENDING = "descending"
    VOLATILE = "volatile"  # first-class value — volatility is named, not hidden


class ConsoleLayout(str, Enum):
    CRYSTAL = "crystal"
    CHAT = "chat"
    ORB = "orb"
    MINIMAL = "minimal"
    FULL = "full"


@dataclass
class LCIRecord:
    """Per-session LCI (Life Coherence Index) snapshot."""
    session_id: str
    phi: float           # coherence score for this session
    force: str           # Spectral Force
    stage: str           # MagnumOpus stage
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class SessionCadenceRecord:
    """When does this GAIAN typically engage?"""
    preferred_hours: list[int]     # 0–23 UTC hours most active
    avg_session_duration: float    # minutes
    longest_session: float         # minutes


@dataclass
class OrbParamOverride:
    """Per-profile orb customization."""
    color_override: Optional[str] = None   # hex color
    size_scale: Optional[float] = None     # 0.5–2.0 multiplier
    pulse_rate: Optional[float] = None     # beats per minute


@dataclass
class GAIANProfileModel:
    """
    Python-side GAIAN profile model.
    Consumed by the backend runtime; TypeScript mirror in src/gaian/GAIANProfile.ts.

    TODO (Issue #756, Phase 1 C27-IMPL-003 analog):
    - Add to runtimetypes.py
    - Implement GAIANProfileManager (load/save/createFromBirth/recordSession)
    - Extend RuntimeContext with profile injection
    """
    architect_id: str
    display_name: str
    birth_timestamp: str            # ISO 8601
    birth_force: str
    birth_stage: str

    lci_baseline: float = 0.0      # rolling 30-session average phi
    lci_history: list[LCIRecord] = field(default_factory=list)
    lci_trend: LCITrend = LCITrend.STABLE

    console_layout: ConsoleLayout = ConsoleLayout.CRYSTAL
    theme: str = "viriditas_default"
    orb_params: OrbParamOverride = field(default_factory=OrbParamOverride)

    preferred_forces: list[str] = field(default_factory=list)
    preferred_stages: list[str] = field(default_factory=list)
    query_patterns: list[str] = field(default_factory=list)
    session_cadence: Optional[SessionCadenceRecord] = None

    total_sessions: int = 0
    last_session_timestamp: Optional[str] = None
    last_known_phi: float = 0.0
    last_known_force: str = ""
    last_known_stage: str = ""

    akashic_loaded: bool = False
    akashic_version: str = ""


@dataclass
class PersonalizationSignal:
    """
    Derived from GAIANProfile and injected into RAGPipeline.query().
    Makes every response actually personalized to this GAIAN's history,
    not just their current phi.

    TODO (Issue #756, Phase 2): Extend RAGPipeline.query() to accept this.
    """
    architect_id: str
    lci_baseline: float
    lci_trend: str
    preferred_forces: list[str]
    preferred_stages: list[str]
    query_patterns: list[str]
    console_layout: str
