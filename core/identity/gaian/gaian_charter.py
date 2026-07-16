"""
core/identity/gaian/gaian_charter.py

GaianCharter — the sovereign rule set that governs all Gaian nodes.

Rules are evaluated in priority order (lower = first).
First non-ABSTAIN verdict wins. Default verdict is DENY (secure by default).

Built-in rules enforce: C01 (inactive deny, root allow),
C08 (observer readonly), C03 (capability required).

Canon Refs: C01, C03, C08, C15
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from .gaian_node import GaianNode, NodeRole


class RuleVerdict(str, Enum):
    ALLOW   = "allow"
    DENY    = "deny"
    ABSTAIN = "abstain"


RuleEvaluator = Callable[[GaianNode, str, Optional[str], Dict[str, Any]], RuleVerdict]


@dataclass
class CharterRule:
    name: str
    priority: int
    evaluator: RuleEvaluator
    canon_ref: str = ""
    description: str = ""
    created_at: float = field(default_factory=time.time)


@dataclass
class CharterDecision:
    verdict: RuleVerdict
    rule_name: str
    node_id: str
    action: str
    resource: Optional[str]
    decided_at: float = field(default_factory=time.time)
    context: Dict[str, Any] = field(default_factory=dict)

    @property
    def allowed(self) -> bool:
        return self.verdict == RuleVerdict.ALLOW


# ---------------------------------------------------------------------------
# Built-in rule evaluators
# ---------------------------------------------------------------------------

def _rule_inactive_node(node: GaianNode, action: str, resource: Optional[str], ctx: Dict[str, Any]) -> RuleVerdict:
    return RuleVerdict.DENY if not node.active else RuleVerdict.ABSTAIN


def _rule_root_unrestricted(node: GaianNode, action: str, resource: Optional[str], ctx: Dict[str, Any]) -> RuleVerdict:
    return RuleVerdict.ALLOW if node.role == NodeRole.ROOT else RuleVerdict.ABSTAIN


def _rule_observer_readonly(node: GaianNode, action: str, resource: Optional[str], ctx: Dict[str, Any]) -> RuleVerdict:
    if node.role == NodeRole.OBSERVER:
        return RuleVerdict.ALLOW if (action.startswith("read") or action.startswith("get") or action == "witness") else RuleVerdict.DENY
    return RuleVerdict.ABSTAIN


def _rule_capability_required(node: GaianNode, action: str, resource: Optional[str], ctx: Dict[str, Any]) -> RuleVerdict:
    if node.role == NodeRole.ROOT:
        return RuleVerdict.ABSTAIN
    if node.has_capability(action, resource):
        return RuleVerdict.ALLOW
    if "." in action:
        ns = action.split(".")[0] + ".*"
        if node.has_capability(ns, resource):
            return RuleVerdict.ALLOW
    return RuleVerdict.DENY


_BUILTIN_RULES: List[CharterRule] = [
    CharterRule(name="inactive-node-deny",  priority=0,  evaluator=_rule_inactive_node,       canon_ref="C01", description="Inactive nodes may not perform any action."),
    CharterRule(name="root-unrestricted",    priority=10, evaluator=_rule_root_unrestricted,   canon_ref="C01", description="ROOT nodes have full sovereign authority."),
    CharterRule(name="observer-readonly",    priority=20, evaluator=_rule_observer_readonly,   canon_ref="C08", description="OBSERVER nodes may only read."),
    CharterRule(name="capability-required",  priority=50, evaluator=_rule_capability_required, canon_ref="C03", description="Non-ROOT nodes must hold a matching capability."),
]


# ---------------------------------------------------------------------------
# GaianCharter
# ---------------------------------------------------------------------------

class GaianCharter:
    DEFAULT_VERDICT = RuleVerdict.DENY

    def __init__(self, include_builtins: bool = True) -> None:
        self._rules: List[CharterRule] = []
        if include_builtins:
            self._rules.extend(_BUILTIN_RULES)
        self._sort()

    def add_rule(self, rule: CharterRule) -> None:
        self._rules.append(rule)
        self._sort()

    def remove_rule(self, name: str) -> bool:
        before = len(self._rules)
        self._rules = [r for r in self._rules if r.name != name]
        return len(self._rules) < before

    def get_rule(self, name: str) -> Optional[CharterRule]:
        return next((r for r in self._rules if r.name == name), None)

    def rules(self) -> List[CharterRule]:
        return list(self._rules)

    def evaluate(self, node: GaianNode, action: str, resource: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> CharterDecision:
        ctx = context or {}
        for rule in self._rules:
            verdict = rule.evaluator(node, action, resource, ctx)
            if verdict != RuleVerdict.ABSTAIN:
                return CharterDecision(verdict=verdict, rule_name=rule.name, node_id=node.id, action=action, resource=resource, context=ctx)
        return CharterDecision(verdict=self.DEFAULT_VERDICT, rule_name="default-deny", node_id=node.id, action=action, resource=resource, context=ctx)

    def is_allowed(self, node: GaianNode, action: str, resource: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> bool:
        return self.evaluate(node, action, resource, context).allowed

    def audit(self, node: GaianNode, actions: List[str], resource: Optional[str] = None) -> Dict[str, CharterDecision]:
        return {action: self.evaluate(node, action, resource) for action in actions}

    def _sort(self) -> None:
        self._rules.sort(key=lambda r: r.priority)
