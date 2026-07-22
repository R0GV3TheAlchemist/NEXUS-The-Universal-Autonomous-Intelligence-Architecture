"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  NEXUS — The Universal Autonomous Intelligence Architecture
  Author   : Kyle Steen
  GitHub   : R0GV3TheAlchemist
  Email    : xxkylesteenxx@outlook.com
  License  : All Rights Reserved © 2026 Kyle Steen
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

dao.py — NEXUS Decentralized Autonomous Organization Engine.

Implements Proposal lifecycle, Vote casting, quorum enforcement,
and hash-verifiable ProposalResult audit trails.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional
from uuid import UUID, uuid4
import hashlib, json, time


class ProposalStatus(Enum):
    DRAFT    = auto()
    OPEN     = auto()
    CLOSED   = auto()
    PASSED   = auto()
    REJECTED = auto()
    VETOED   = auto()


class ProposalTier(Enum):
    CONSTITUTIONAL = 0   # quorum 75%, supermajority 80%
    POLICY         = 1   # quorum 51%, supermajority 66%
    OPERATIONAL    = 2   # quorum 33%, supermajority 51%


QUORUM_RULES: Dict[ProposalTier, Dict[str, float]] = {
    ProposalTier.CONSTITUTIONAL: {"quorum": 0.75, "supermajority": 0.80},
    ProposalTier.POLICY:         {"quorum": 0.51, "supermajority": 0.66},
    ProposalTier.OPERATIONAL:    {"quorum": 0.33, "supermajority": 0.51},
}


@dataclass
class Vote:
    """A single vote cast by a registered voter."""
    vote_id:     UUID  = field(default_factory=uuid4)
    voter_id:    UUID  = field(default_factory=uuid4)
    proposal_id: UUID  = field(default_factory=uuid4)
    in_favor:    bool  = True
    weight:      float = 1.0
    timestamp:   float = field(default_factory=time.time)
    rationale:   str   = ""


@dataclass
class Proposal:
    """A governance proposal submitted for DAO vote."""
    proposal_id:  UUID           = field(default_factory=uuid4)
    title:        str            = ""
    description:  str            = ""
    proposer_id:  UUID           = field(default_factory=uuid4)
    tier:         ProposalTier   = ProposalTier.OPERATIONAL
    status:       ProposalStatus = ProposalStatus.DRAFT
    opens_at:     float          = 0.0
    closes_at:    float          = 0.0
    created_at:   float          = field(default_factory=time.time)
    votes:        List[Vote]     = field(default_factory=list)
    metadata:     dict           = field(default_factory=dict)

    def cast_vote(self, vote: Vote) -> None:
        if self.status != ProposalStatus.OPEN:
            raise ValueError(
                f"Cannot vote on proposal in status {self.status.name}")
        self.votes.append(vote)

    def total_weight(self) -> float:
        return sum(v.weight for v in self.votes)

    def favor_weight(self) -> float:
        return sum(v.weight for v in self.votes if v.in_favor)


@dataclass
class ProposalResult:
    """Immutable, hash-verified result of a closed proposal."""
    result_id:     UUID   = field(default_factory=uuid4)
    proposal_id:   UUID   = field(default_factory=uuid4)
    status:        str    = ""
    total_weight:  float  = 0.0
    favor_weight:  float  = 0.0
    quorum_met:    bool   = False
    majority_met:  bool   = False
    closed_at:     float  = field(default_factory=time.time)
    hash:          str    = ""

    def compute_hash(self) -> str:
        payload = json.dumps({
            "result_id":    str(self.result_id),
            "proposal_id":  str(self.proposal_id),
            "status":       self.status,
            "total_weight": self.total_weight,
            "favor_weight": self.favor_weight,
            "closed_at":    self.closed_at,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()


class DAOEngine:
    """
    NEXUS DAO Engine — manages proposal lifecycle, vote tallying,
    quorum enforcement, and result publication.
    """

    def __init__(self, total_eligible_weight: float = 100.0) -> None:
        self.total_eligible_weight = total_eligible_weight
        self._proposals: Dict[UUID, Proposal] = {}
        self._results:   Dict[UUID, ProposalResult] = {}

    def submit(self, proposal: Proposal) -> None:
        proposal.status = ProposalStatus.DRAFT
        self._proposals[proposal.proposal_id] = proposal

    def open_voting(self, proposal_id: UUID,
                    duration_seconds: float = 86400.0) -> None:
        proposal = self._get(proposal_id)
        proposal.status    = ProposalStatus.OPEN
        proposal.opens_at  = time.time()
        proposal.closes_at = proposal.opens_at + duration_seconds

    def close_voting(self, proposal_id: UUID) -> None:
        proposal = self._get(proposal_id)
        proposal.status = ProposalStatus.CLOSED

    def tally(self, proposal_id: UUID) -> ProposalResult:
        """Tally votes, enforce quorum/supermajority, publish result."""
        proposal = self._get(proposal_id)
        if proposal.status not in (ProposalStatus.CLOSED, ProposalStatus.OPEN):
            raise ValueError("Proposal must be CLOSED or OPEN to tally.")

        rules         = QUORUM_RULES[proposal.tier]
        total         = proposal.total_weight()
        favor         = proposal.favor_weight()
        participation = total / self.total_eligible_weight if \
            self.total_eligible_weight > 0 else 0.0

        quorum_met   = participation >= rules["quorum"]
        majority_met = (favor / total >= rules["supermajority"]) if total > 0 else False

        final_status = ProposalStatus.PASSED if (quorum_met and majority_met) \
            else ProposalStatus.REJECTED

        proposal.status = final_status
        result = ProposalResult(
            proposal_id=proposal_id,
            status=final_status.name,
            total_weight=total,
            favor_weight=favor,
            quorum_met=quorum_met,
            majority_met=majority_met,
        )
        result.hash = result.compute_hash()
        self._results[proposal_id] = result
        return result

    def veto(self, proposal_id: UUID) -> None:
        self._get(proposal_id).status = ProposalStatus.VETOED

    def get_result(self, proposal_id: UUID) -> Optional[ProposalResult]:
        return self._results.get(proposal_id)

    def list_proposals(self,
                       status: Optional[ProposalStatus] = None) -> List[Proposal]:
        proposals = list(self._proposals.values())
        if status:
            proposals = [p for p in proposals if p.status == status]
        return proposals

    def _get(self, proposal_id: UUID) -> Proposal:
        p = self._proposals.get(proposal_id)
        if p is None:
            raise KeyError(f"Proposal not found: {proposal_id}")
        return p
