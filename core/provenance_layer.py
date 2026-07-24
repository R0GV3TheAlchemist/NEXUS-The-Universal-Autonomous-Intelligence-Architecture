# Copyright © 2025–2026 Kyle Alexander Steen. All rights reserved. AGPL-3.0.
"""
Provenance Layer — Capability Domain 21

Every piece of GAIA knowledge answers:
  Where did I learn this? Who verified it? When? Which version?
  Which simulation? Which paper? Which sensor?

Knowledge without provenance becomes unauditable.

Related: Issue #753 Tier 3 Domain 21 (Provenance Layer)
Partial existing: core/rag/ source attribution
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class ProvenanceSourceType(str, Enum):
    RAG_DOCUMENT = "RAG_DOCUMENT"       # Retrieved from RAG pipeline
    SENSOR = "SENSOR"                   # IoT / physical sensor
    SIMULATION = "SIMULATION"           # GAIA simulation output
    HUMAN_INPUT = "HUMAN_INPUT"         # Provided by a human
    AGENT_INFERENCE = "AGENT_INFERENCE" # Inferred by a GAIAN
    EXTERNAL_API = "EXTERNAL_API"       # External data source
    CANON = "CANON"                     # GAIA Canon document
    AUDIT_LOG = "AUDIT_LOG"             # C27 audit log


@dataclass
class ProvenanceRecord:
    """
    Complete provenance metadata for a piece of knowledge or output.

    Answers: Where did this come from? Who verified it? When? How confident?
    """
    record_id: str
    claim: str              # The knowledge claim being attributed
    source_type: ProvenanceSourceType
    source_id: str          # Document ID, sensor ID, session ID, etc.
    source_version: Optional[str] = None
    verified_by: Optional[str] = None    # Principal who verified
    verified_at: Optional[datetime] = None
    recorded_at: datetime = field(default_factory=datetime.utcnow)
    confidence: float = 1.0
    chain: list[str] = field(default_factory=list)  # upstream provenance IDs


class ProvenanceLayer:
    """
    Attaches and retrieves provenance records for GAIA knowledge.

    TODO (Issue #753 Domain 21):
    - Integrate with core/rag/ source attribution
    - Attach provenance to all RAGPipeline outputs
    - Build provenance chain for multi-hop inferences
    - Cross-reference with UncertaintyLayer (Domain 20)
    """

    def record(
        self,
        claim: str,
        source_type: ProvenanceSourceType,
        source_id: str,
        confidence: float = 1.0,
        source_version: Optional[str] = None,
        verified_by: Optional[str] = None,
    ) -> ProvenanceRecord:
        """
        Record provenance for a knowledge claim.
        TODO: implement — Issue #753 Domain 21
        """
        raise NotImplementedError("ProvenanceLayer.record — Issue #753 Domain 21")

    def retrieve(self, claim: str) -> list[ProvenanceRecord]:
        """
        Retrieve all provenance records for a claim.
        TODO: implement
        """
        raise NotImplementedError("ProvenanceLayer.retrieve — Issue #753 Domain 21")
