# Copyright (c) 2026 R0GV3 The Alchemist
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
core/error_correction/models.py

Normalized error record for GAIA's Error Correction Detection Layer.

Every error source — Ruff, Black, isort, custom Canon rules, future
SAST tools — is normalized into a single GAIAErrorFinding so the
detector, reporter, and (Phase 2) auto-repair layers all speak one
language regardless of where the finding originated.

Canon Ref: C01 (Sovereignty), C30 (No silent failures), Issue #755
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


# ------------------------------------------------------------------ #
#  Enums                                                              #
# ------------------------------------------------------------------ #

class GAIASeverity(str, Enum):
    """Severity levels aligned with GAIA Canon priority tiers."""
    CRITICAL = "critical"   # blocks merge / Canon violation
    HIGH     = "high"       # should fix before merge
    MEDIUM   = "medium"     # fix in same sprint
    LOW      = "low"        # style / formatting
    INFO     = "info"       # informational, no action required


class GAIAErrorCategory(str, Enum):
    """Category of the finding — determines repair strategy in Phase 2."""
    SYNTAX          = "syntax"           # parse / syntax error
    LINT            = "lint"             # ruff lint rule
    FORMAT          = "format"           # black / ruff-format
    IMPORT_ORDER    = "import_order"     # isort
    TYPE            = "type"             # mypy / pyright
    SECURITY        = "security"         # bandit / CodeQL
    CANON_VIOLATION = "canon_violation"  # GAIA-specific architectural rule
    COPYRIGHT       = "copyright"        # missing copyright header
    DEPENDENCY      = "dependency"       # pip-audit / vulnerable dep
    UNKNOWN         = "unknown"          # unclassified


# ------------------------------------------------------------------ #
#  Core Finding Dataclass                                             #
# ------------------------------------------------------------------ #

@dataclass
class GAIAErrorFinding:
    """
    A single normalized error finding from any GAIA error detection source.

    Fields
    ------
    rule_id       : Tool-native rule identifier (e.g. "E501", "B006", "CANON-01").
    message       : Human-readable description of the finding.
    file_path     : Repo-relative path to the affected file.
    source        : Name of the tool that produced this finding (e.g. "ruff").
    category      : Broad classification — determines Phase 2 repair strategy.
    severity      : How urgently this needs to be addressed.
    line          : 1-based line number (None if file-level).
    col           : 1-based column number (None if not applicable).
    end_line      : Last line of the affected range (None if single-line).
    end_col       : Last column of the affected range (None if not applicable).
    fix_available : True when the source tool can auto-apply a fix.
    fix_diff      : Unified diff of the proposed fix (None if unavailable).
    confidence    : Float 0.0–1.0 expressing certainty of the finding.
                    Ruff findings with fix_available=True → 1.0;
                    fix_available=False → 0.9 (prefer human review in Phase 2).
    provenance    : Free-form dict for Provenance Layer metadata (Issue #753).
    detected_at   : UTC timestamp of detection.
    """

    # Required fields
    rule_id:    str
    message:    str
    file_path:  str
    source:     str
    category:   GAIAErrorCategory
    severity:   GAIASeverity

    # Location (optional — some findings are file-level)
    line:     Optional[int] = None
    col:      Optional[int] = None
    end_line: Optional[int] = None
    end_col:  Optional[int] = None

    # Repair metadata
    fix_available: bool            = False
    fix_diff:      Optional[str]   = None
    confidence:    float           = 1.0

    # Provenance (Provenance Layer — Issue #753)
    provenance: dict = field(default_factory=dict)

    # Timestamp
    detected_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # ---------------------------------------------------------------- #
    #  Derived helpers                                                  #
    # ---------------------------------------------------------------- #

    def location_str(self) -> str:
        """Human-readable location string e.g. 'core/foo.py:42:5'."""
        if self.line is None:
            return self.file_path
        if self.col is None:
            return f"{self.file_path}:{self.line}"
        return f"{self.file_path}:{self.line}:{self.col}"

    def is_blocking(self) -> bool:
        """True when this finding should block a merge."""
        return self.severity in (GAIASeverity.CRITICAL, GAIASeverity.HIGH)

    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dict for artifact reports."""
        return {
            "rule_id":       self.rule_id,
            "message":       self.message,
            "file_path":     self.file_path,
            "source":        self.source,
            "category":      self.category.value,
            "severity":      self.severity.value,
            "line":          self.line,
            "col":           self.col,
            "end_line":      self.end_line,
            "end_col":       self.end_col,
            "fix_available": self.fix_available,
            "fix_diff":      self.fix_diff,
            "confidence":    self.confidence,
            "provenance":    self.provenance,
            "detected_at":   self.detected_at.isoformat(),
            "location":      self.location_str(),
            "blocking":      self.is_blocking(),
        }

    @classmethod
    def from_ruff_diagnostic(cls, diag: dict, file_path: str) -> "GAIAErrorFinding":
        """
        Construct a GAIAErrorFinding from a single Ruff JSON diagnostic entry.

        Ruff JSON shape (ruff check --output-format json):
        {
          "code":     "E501",
          "message":  "Line too long (92 > 88)",
          "filename": "core/foo.py",
          "location": {"row": 10, "column": 1},
          "end_location": {"row": 10, "column": 92},
          "fix":      {"edits": [...]}   # present when auto-fixable
        }

        confidence is set to 1.0 when a machine fix is available, and 0.9
        otherwise — signalling to the Phase 2 repair layer that human review
        is preferred for findings without an automatic fix.
        """
        code      = diag.get("code") or "RUFF"
        has_fix   = bool(diag.get("fix"))
        loc       = diag.get("location") or {}
        end_loc   = diag.get("end_location") or {}

        return cls(
            rule_id=code,
            message=diag.get("message", ""),
            file_path=file_path,
            source="ruff",
            category=_ruff_category(code),
            severity=_ruff_severity(code),
            line=loc.get("row"),
            col=loc.get("column"),
            end_line=end_loc.get("row"),
            end_col=end_loc.get("column"),
            fix_available=has_fix,
            confidence=1.0 if has_fix else 0.9,
            provenance={"tool": "ruff", "rule": code},
        )


# ------------------------------------------------------------------ #
#  Ruff rule → category / severity mapping                           #
# ------------------------------------------------------------------ #

def _ruff_category(code: str) -> GAIAErrorCategory:
    """
    Map a Ruff rule code prefix to a GAIAErrorCategory.

    Two-character prefixes are checked first to handle multi-char Ruff
    rule families (RUF, PL, PT, UP, ANN) before falling back to the
    single-character map.
    """
    two_char = code[:2].upper()
    two_char_mapping: dict[str, GAIAErrorCategory] = {
        "RU": GAIAErrorCategory.LINT,        # RUF — Ruff-native rules
        "PL": GAIAErrorCategory.LINT,        # PL  — Pylint
        "PT": GAIAErrorCategory.LINT,        # PT  — pytest style
        "UP": GAIAErrorCategory.LINT,        # UP  — pyupgrade
        "AN": GAIAErrorCategory.TYPE,        # ANN — annotations / type hints
    }
    if two_char in two_char_mapping:
        return two_char_mapping[two_char]

    prefix = code[:1].upper()
    one_char_mapping: dict[str, GAIAErrorCategory] = {
        "E": GAIAErrorCategory.LINT,
        "W": GAIAErrorCategory.LINT,
        "F": GAIAErrorCategory.LINT,
        "I": GAIAErrorCategory.IMPORT_ORDER,
        "N": GAIAErrorCategory.LINT,
        "D": GAIAErrorCategory.LINT,
        "S": GAIAErrorCategory.SECURITY,
        "B": GAIAErrorCategory.LINT,
        "C": GAIAErrorCategory.LINT,
        "T": GAIAErrorCategory.LINT,
        "Q": GAIAErrorCategory.FORMAT,
        "U": GAIAErrorCategory.LINT,
        "A": GAIAErrorCategory.LINT,
        "G": GAIAErrorCategory.LINT,
    }
    return one_char_mapping.get(prefix, GAIAErrorCategory.UNKNOWN)


def _ruff_severity(code: str) -> GAIASeverity:
    """
    Map a Ruff rule code to a GAIASeverity.

    Order matters — more specific prefixes are checked first.
    """
    # Syntax / parse errors — always critical
    if code.startswith(("E9", "F8", "F7")):
        return GAIASeverity.CRITICAL
    # Undefined name / redefined name — runtime risk, block merge
    if code in ("F821", "F811"):
        return GAIASeverity.HIGH
    # Security rules — block merge
    if code.startswith("S"):
        return GAIASeverity.HIGH
    # Style / formatting / import order — low priority
    if code.startswith(("E1", "E2", "E3", "E4", "E5", "W", "Q", "I")):
        return GAIASeverity.LOW
    return GAIASeverity.MEDIUM
