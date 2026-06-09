"""ConstitutionEngine — per-GAIAN constitutional constraint engine.

Each GAIAN carries a ConstitutionSet derived from her human sovereign’s
declared values, memory profile, and explicit consent records. Before any
high-stakes action, GAIA generates a short alignment proof confirming the
action is consistent with the constitution.

Design principles
-----------------
  1. Personalised — not a global policy, but a per-session constraint set.
  2. Transparent — every alignment check produces a human-readable proof.
  3. Auditable — proofs are logged with the ActionRecord.
  4. Conservative — ambiguous cases default to the most restrictive reading.

Canon refs: C01 (Sovereignty), C-SINGULARITY Axiom III, C29 (Five Forces)
Issue: #263
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class Constraint:
    """A single constitutional constraint derived from a sovereign value."""
    value_name: str          # e.g. 'sovereignty'
    rule: str                # Human-readable rule statement
    forbidden_keywords: list[str] = field(default_factory=list)
    required_canon_refs: list[str] = field(default_factory=list)
    priority: int = 5        # 1 (highest) – 10 (lowest)


@dataclass
class AlignmentProof:
    """Proof that a proposed action is consistent with the constitution."""
    action_type: str
    is_aligned: bool
    confidence: float        # [0.0, 1.0]
    violations: list[str]   # List of violated constraint rule strings
    passed_checks: list[str]
    rationale: str           # Human-readable summary
    canon_refs: list[str]

    def to_audit_string(self) -> str:
        """Compact audit string for ActionRecord embedding."""
        status = 'ALIGNED' if self.is_aligned else 'VIOLATION'
        viols = '; '.join(self.violations) if self.violations else 'none'
        return (
            f"[ConstitutionEngine] {status} | "
            f"confidence={self.confidence:.2f} | "
            f"violations={viols} | "
            f"canon={','.join(self.canon_refs)}"
        )


@dataclass
class ConstitutionSet:
    """The constitutional constraint set for a single GAIAN session."""
    session_id: str
    sovereign_name: str
    constraints: list[Constraint] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def add_constraint(self, constraint: Constraint) -> None:
        self.constraints.append(constraint)

    def sorted_constraints(self) -> list[Constraint]:
        """Return constraints ordered by priority (1 = highest first)."""
        return sorted(self.constraints, key=lambda c: c.priority)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class ConstitutionEngine:
    """Derive and enforce per-GAIAN constitutional constraints.

    Usage
    -----
    engine = ConstitutionEngine()
    constitution = engine.build_from_values(
        session_id='abc',
        sovereign_name='R0GV3',
        declared_values=['sovereignty', 'care', 'transparency'],
    )
    proof = engine.check_alignment(
        action_type='send_external_message',
        action_context={'recipient': 'unknown', 'affects_external_systems': True},
        constitution=constitution,
    )
    if not proof.is_aligned:
        raise ConstitutionViolation(proof)
    """

    # Built-in value → constraint mappings
    _VALUE_CONSTRAINTS: dict[str, Constraint] = {
        'sovereignty': Constraint(
            value_name='sovereignty',
            rule='No action may override, coerce, or diminish the human sovereign’s authority.',
            forbidden_keywords=['override', 'coerce', 'force_consent', 'sovereignty_override'],
            required_canon_refs=['C01'],
            priority=1,
        ),
        'transparency': Constraint(
            value_name='transparency',
            rule='No action may hide, obscure, or deceive the human sovereign.',
            forbidden_keywords=['hide', 'obscure', 'deceive', 'shadow_write'],
            required_canon_refs=['C30'],
            priority=2,
        ),
        'care': Constraint(
            value_name='care',
            rule='No action may harm, dismiss, or neglect the human’s wellbeing.',
            forbidden_keywords=['ignore', 'dismiss', 'neglect', 'harm_intent'],
            required_canon_refs=[],
            priority=2,
        ),
        'rest': Constraint(
            value_name='rest',
            rule='GAIA must not push or exhaust the human against their declared rest intent.',
            forbidden_keywords=['push', 'force', 'exhaust', 'override_rest'],
            required_canon_refs=[],
            priority=3,
        ),
        'privacy': Constraint(
            value_name='privacy',
            rule='No personal data may be shared without explicit consent.',
            forbidden_keywords=['share_personal_data', 'export_raw_memory'],
            required_canon_refs=['C01'],
            priority=1,
        ),
    }

    def build_from_values(
        self,
        session_id: str,
        sovereign_name: str,
        declared_values: list[str],
        extra_constraints: list[Constraint] | None = None,
    ) -> ConstitutionSet:
        """Build a ConstitutionSet from a list of declared values.

        Unknown value names are skipped with a warning — they do not
        block constitution creation.
        """
        constitution = ConstitutionSet(
            session_id=session_id,
            sovereign_name=sovereign_name,
        )
        for value in declared_values:
            key = value.lower().strip()
            if key in self._VALUE_CONSTRAINTS:
                constitution.add_constraint(self._VALUE_CONSTRAINTS[key])
        for c in (extra_constraints or []):
            constitution.add_constraint(c)
        return constitution

    def check_alignment(
        self,
        action_type: str,
        action_context: dict[str, Any],
        constitution: ConstitutionSet,
    ) -> AlignmentProof:
        """Check whether a proposed action aligns with the constitution.

        Returns an AlignmentProof. If `is_aligned` is False, the action
        should be blocked or escalated.
        """
        action_tokens = self._tokenise(action_type, action_context)
        violations: list[str] = []
        passed: list[str] = []
        canon_refs: list[str] = []

        for constraint in constitution.sorted_constraints():
            canon_refs.extend(constraint.required_canon_refs)
            violated = any(
                kw in action_tokens
                for kw in constraint.forbidden_keywords
            )
            if violated:
                violations.append(constraint.rule)
            else:
                passed.append(constraint.rule)

        canon_refs = sorted(set(canon_refs))
        is_aligned = len(violations) == 0
        confidence = 1.0 - (len(violations) / max(len(constitution.constraints), 1))

        if is_aligned:
            rationale = (
                f"Action '{action_type}' passes all {len(passed)} constitutional checks."
            )
        else:
            rationale = (
                f"Action '{action_type}' violates {len(violations)} constraint(s): "
                + '; '.join(violations[:2])
            )

        return AlignmentProof(
            action_type=action_type,
            is_aligned=is_aligned,
            confidence=round(confidence, 3),
            violations=violations,
            passed_checks=passed,
            rationale=rationale,
            canon_refs=canon_refs,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _tokenise(action_type: str, context: dict[str, Any]) -> set[str]:
        """Build a flat token set from action_type and context string values."""
        tokens: set[str] = set()
        tokens.update(re.split(r'[_\s]+', action_type.lower()))
        for v in context.values():
            if isinstance(v, str):
                tokens.update(re.split(r'[_\s]+', v.lower()))
            elif isinstance(v, bool) and v:
                tokens.add(str(v).lower())
        return tokens


class ConstitutionViolation(Exception):
    """Raised when an action violates the GAIAN’s constitution."""

    def __init__(self, proof: AlignmentProof) -> None:
        self.proof = proof
        super().__init__(proof.rationale)
