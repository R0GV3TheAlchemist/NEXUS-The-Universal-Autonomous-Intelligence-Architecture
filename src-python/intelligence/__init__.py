"""
intelligence — NEXUS Intelligence Layer Package
================================================
Reference: NEXUS_UNIVERSAL_OS.md § Domain 2 — Intelligence Layer

This package implements the cognitive kernel, agent lifecycle, perception
pipeline, knowledge graph, and explainability layer for NEXUS.

The AuditLog class is designed for clean import by nexus_os.kernel
without circular dependencies — it depends only on the standard library.

All behaviour is governed by GAIAN_LAWS.md and ETHICS.md.

© 2026 Kyle Alexander Steen (The Alchemist). All rights reserved.
SPDX-License-Identifier: AGPL-3.0-only
"""

__version__ = "0.1.0"
__author__ = "Kyle Alexander Steen"
__copyright__ = "© 2026 Kyle Alexander Steen (The Alchemist). All rights reserved."

from intelligence.cognitive_kernel import GoalStack, ReasoningEngine, AuditLog
from intelligence.agent import BaseAgent, AgentLifecycle, AgentCoalition
from intelligence.perception import SensorFusion, WorldModel, UncertaintyQuantifier
from intelligence.knowledge_graph import EpisodicMemory, SemanticMemory, ProceduralMemory
from intelligence.explainability import DecisionTrace, ExplanationSummary

__all__ = [
    "GoalStack",
    "ReasoningEngine",
    "AuditLog",
    "BaseAgent",
    "AgentLifecycle",
    "AgentCoalition",
    "SensorFusion",
    "WorldModel",
    "UncertaintyQuantifier",
    "EpisodicMemory",
    "SemanticMemory",
    "ProceduralMemory",
    "DecisionTrace",
    "ExplanationSummary",
]
