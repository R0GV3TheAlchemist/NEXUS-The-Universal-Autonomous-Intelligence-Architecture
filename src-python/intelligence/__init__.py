"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NEXUS — The Universal Autonomous Intelligence Architecture
  GAIA  — The Global Autonomous Intelligence Architecture

  Author   : Kyle Steen
  GitHub   : R0GV3TheAlchemist (https://github.com/R0GV3TheAlchemist)
  Email    : xxkylesteenxx@outlook.com
  Project  : NEXUS / GAIA
  License  : All Rights Reserved © 2026 Kyle Steen
             Unauthorized use, reproduction, or distribution
             of this file or its contents is strictly prohibited.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

intelligence — NEXUS Intelligence Layer Package.

Provides the cognitive kernel, agent framework, perception system,
knowledge graph, and explainability subsystem.
"""

__version__ = "1.0.0"
__author__ = "Kyle Steen"
__all__ = [
    "CognitiveKernel",
    "BaseAgent",
    "AgentCoalition",
    "SensorFusion",
    "EpisodicMemory",
    "SemanticMemory",
    "ProceduralMemory",
    "DecisionTrace",
    "ExplanationSummary",
]

from intelligence.cognitive_kernel import CognitiveKernel
from intelligence.agent import BaseAgent, AgentCoalition
from intelligence.perception import SensorFusion
from intelligence.knowledge_graph import EpisodicMemory, SemanticMemory, ProceduralMemory
from intelligence.explainability import DecisionTrace, ExplanationSummary
