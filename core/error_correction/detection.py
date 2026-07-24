# Copyright © 2025–2026 Kyle Alexander Steen. All rights reserved. AGPL-3.0.
"""
Error Correction Engine — Detection Layer

Normalizes findings from multiple tools (Ruff, static analysis, test harness,
architectural rules) into a common GAIAErrorFinding model.

Related: Issue #755 Phase 1
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class ErrorSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ErrorCategory(str, Enum):
    STYLE = "STYLE"                   # Lint / formatting
    BUG = "BUG"                       # Logic errors
    SECURITY = "SECURITY"             # SAST findings
    ARCHITECTURE = "ARCHITECTURE"     # Canon/GAIA rule violations
    DEAD_CODE = "DEAD_CODE"           # Unreachable code
    TYPE_ERROR = "TYPE_ERROR"         # Type annotation violations


@dataclass
class GAIAErrorFinding:
    """
    Normalized finding from the Detection Layer.
    All tools produce this common model before entering the repair pipeline.
    """
    finding_id: str
    file_path: str
    line: Optional[int]
    column: Optional[int]
    severity: ErrorSeverity
    category: ErrorCategory
    rule_id: str            # e.g. "E501", "GAIA-ARCH-001"
    message: str
    source_tool: str        # "ruff", "semgrep", "pytest", "gaia_arch_linter"
    confidence: float       # 0.0–1.0
    detected_at: datetime = field(default_factory=datetime.utcnow)
    snippet: Optional[str] = None


class DetectionLayer:
    """
    Runs all detection tools and normalizes findings.

    TODO (Issue #755 Phase 1):
    - Integrate Ruff
    - Define GAIAErrorFinding schema
    - Add basic architectural rule checks (missing copyright headers, etc.)
    - No auto-fixes yet — detection and documentation only in Phase 1
    """

    def scan(self, paths: list[str]) -> list[GAIAErrorFinding]:
        """
        Run all configured detection tools across the given paths.
        Returns normalized findings.
        TODO: implement — Issue #755 Phase 1
        """
        raise NotImplementedError("DetectionLayer.scan — Issue #755 Phase 1")
