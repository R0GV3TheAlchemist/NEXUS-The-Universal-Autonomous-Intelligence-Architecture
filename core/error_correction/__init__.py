# Copyright (c) 2026 R0GV3 The Alchemist
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
core/error_correction/__init__.py

GAIA Error Correction — Phase 1b: Detection Layer (Ruff + Canon Rules)

Public surface:
    GAIAErrorFinding     — normalized error record
    GAIASeverity         — severity enum
    GAIAErrorCategory    — error category enum
    ErrorDetector        — runs Ruff + CanonChecker, yields GAIAErrorFinding
    CanonChecker         — GAIA architectural Canon rule checker
    ErrorReporter        — writes Markdown + JSON artifact reports

Canon Ref: C01, C30, Issue #755
"""
from core.error_correction.models import (
    GAIAErrorCategory,
    GAIAErrorFinding,
    GAIASeverity,
)
from core.error_correction.canon_checker import CanonChecker
from core.error_correction.detector import ErrorDetector
from core.error_correction.reporter import ErrorReporter

__version__ = "1.0.0"

__all__ = [
    "GAIAErrorFinding",
    "GAIASeverity",
    "GAIAErrorCategory",
    "CanonChecker",
    "ErrorDetector",
    "ErrorReporter",
    "__version__",
]
