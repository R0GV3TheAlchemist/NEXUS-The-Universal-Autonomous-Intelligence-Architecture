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

governance — NEXUS Governance, DAO & Ethics Layer Package.

Provides DAO proposal/vote/result cycles, ethics constraint enforcement,
federation node management, and incident response pipeline.
"""

__version__ = "1.0.0"
__author__ = "Kyle Steen"
__all__ = [
    "DAOEngine",
    "Proposal",
    "Vote",
    "EthicsEngine",
    "EthicsConstraint",
    "ViolationReport",
    "FederationRegistry",
    "FederationNode",
    "ConsensusProtocol",
    "IncidentRecord",
    "IncidentResponsePipeline",
    "OversightQueue",
]

from governance.dao import DAOEngine, Proposal, Vote
from governance.ethics_engine import EthicsEngine, EthicsConstraint, ViolationReport
from governance.federation import FederationRegistry, FederationNode, ConsensusProtocol
from governance.incident import IncidentRecord, IncidentResponsePipeline
from governance.oversight_queue import OversightQueue, OversightItem
