"""
core/canon/canon_entry.py
Canon Entry — atomic unit of knowledge within the GAIA Canon system.

Provides:
  - CanonEntry       : main dataclass
  - CanonEntryError  : exception class
  - RegisterSignal   : semantic register signal enum
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class RegisterSignal(str, Enum):
    """Semantic register signal for a canon entry."""
    EXECUTIVE   = "executive"
    REFLECTIVE  = "reflective"
    MINIMAL     = "minimal"
    UNSPECIFIED = "unspecified"


class CanonEntryError(Exception):
    """Raised when a CanonEntry validation operation fails."""


# Keyword groups used to detect register conflicts
_REGISTER_KEYWORDS: Dict[str, List[str]] = {
    "executive":  ["build", "create", "research", "design", "execute",
                   "develop", "implement", "integrate", "deploy", "launch",
                   "produce", "construct", "engineer", "code", "analyze",
                   "explore", "investigate"],
    "reflective": ["reflect", "contemplate", "meditate", "journal",
                   "inquire", "feel", "sense", "introspect", "wonder",
                   "ponder", "question", "examine", "review"],
    "minimal":    ["rest", "sleep", "pause", "restore", "relax",
                   "breathe", "recover", "slow", "quiet", "stillness",
                   "wait", "cease"],
}

_CANON_REF_RE = re.compile(r"\bC[0-9]{2,}\b")
_ISO8601_RE   = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$"
)


@dataclass
class CanonEntry:
    """An atomic knowledge record in the GAIA Canon."""

    ref_id:          str
    author:          str
    timestamp:       str
    version:         str
    body:            str
    register_signal: RegisterSignal = RegisterSignal.UNSPECIFIED
    tags:            List[str]      = field(default_factory=list)
    metadata:        Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------ #
    #  Validation                                                          #
    # ------------------------------------------------------------------ #

    def validate(self) -> "CanonEntry":
        """Validate and return self. Raises CanonEntryError on failure."""
        if not self.ref_id:
            raise CanonEntryError("ref_id must not be blank")
        if " " in self.ref_id or "\t" in self.ref_id:
            raise CanonEntryError(
                "ref_id must not contain whitespace — use hyphens or underscores"
            )
        if not self.author:
            raise CanonEntryError("author must not be blank")
        if not _ISO8601_RE.match(self.timestamp):
            raise CanonEntryError(
                "timestamp must be a valid ISO-8601 datetime string "
                "(e.g. 2026-06-08T12:00:00Z)"
            )
        if not self.version:
            raise CanonEntryError("version must not be blank")
        if not self.body or not self.body.strip():
            raise CanonEntryError("body must not be blank")
        if len(self.body.strip()) < 10:
            raise CanonEntryError(
                "body is too short — must be at least 10 non-whitespace characters"
            )

        # Keyword-register conflict check (skip for UNSPECIFIED)
        if self.register_signal != RegisterSignal.UNSPECIFIED:
            self._check_register_conflict()

        return self

    def _check_register_conflict(self) -> None:
        body_lower = self.body.lower()
        declared   = self.register_signal.value

        # Find which group the body's dominant keywords belong to
        scores: Dict[str, int] = {g: 0 for g in _REGISTER_KEYWORDS}
        for group, keywords in _REGISTER_KEYWORDS.items():
            for kw in keywords:
                if kw in body_lower:
                    scores[group] += 1

        dominant_group = max(scores, key=lambda g: scores[g])
        if scores[dominant_group] == 0:
            return  # no detectable group — no conflict

        if dominant_group != declared:
            raise CanonEntryError(
                f"Values-alignment conflict: body signals '{dominant_group}' "
                f"but declared register_signal is '{declared}'"
            )

    # ------------------------------------------------------------------ #
    #  Serialisation                                                       #
    # ------------------------------------------------------------------ #

    def to_dict(self) -> dict:
        return {
            "ref_id":          self.ref_id,
            "author":          self.author,
            "timestamp":       self.timestamp,
            "version":         self.version,
            "body":            self.body,
            "register_signal": self.register_signal.value,
            "tags":            self.tags,
            "metadata":        self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CanonEntry":
        raw_signal = data.get("register_signal", RegisterSignal.UNSPECIFIED.value)
        try:
            signal = RegisterSignal(raw_signal)
        except ValueError:
            signal = RegisterSignal.UNSPECIFIED
        return cls(
            ref_id=data.get("ref_id", ""),
            author=data.get("author", ""),
            timestamp=data.get("timestamp", ""),
            version=data.get("version", ""),
            body=data.get("body", ""),
            register_signal=signal,
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )

    # ------------------------------------------------------------------ #
    #  Context helpers                                                     #
    # ------------------------------------------------------------------ #

    def to_context_string(self) -> str:
        return f"[Canon:{self.ref_id}] {self.body}"

    def embedded_canon_refs(self) -> List[str]:
        """Return all Canon ref-IDs (e.g. C01, C32) embedded in the body."""
        return _CANON_REF_RE.findall(self.body)
