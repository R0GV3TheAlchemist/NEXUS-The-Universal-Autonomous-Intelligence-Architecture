# Copyright © 2025–2026 Kyle Alexander Steen. All rights reserved. AGPL-3.0.
"""
core.error_correction — GAIA Automatic Error Correction & Documentation Engine

Three-layer architecture per Issue #755:
    detection   — GAIAErrorFinding, linting, static analysis, architectural rules
    repair      — rule-based, template-based, AI-assisted patch candidates
    reporting   — structured run reports, knowledge promotion hooks

Related: Issue #755
"""
from core.error_correction.detection import GAIAErrorFinding, ErrorSeverity, DetectionLayer
from core.error_correction.repair import RepairLayer, PatchCandidate
from core.error_correction.reporting import ErrorCorrectionReport, ReportingLayer

__all__ = [
    "GAIAErrorFinding",
    "ErrorSeverity",
    "DetectionLayer",
    "RepairLayer",
    "PatchCandidate",
    "ErrorCorrectionReport",
    "ReportingLayer",
]
