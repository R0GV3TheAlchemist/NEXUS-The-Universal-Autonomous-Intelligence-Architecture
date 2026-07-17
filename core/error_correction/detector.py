# Copyright (c) 2026 R0GV3 The Alchemist
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
core/error_correction/detector.py

GAIA Error Correction — Detection Engine (Phase 1b)

Runs all configured detectors:
  1. Ruff          — lint, format, import-order, syntax, security rules
  2. CanonChecker  — GAIA architectural Canon rules (CANON-01 – CANON-08)

Every finding is normalized into a GAIAErrorFinding and sorted by severity.
No files are ever modified here — detection only.

run() results are cached on the instance. Call invalidate_cache() before
re-running (e.g. after Phase 2 auto-repair applies a fix).

Canon Ref: C01, C30, Issue #755 Phase 1b
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Iterator, Optional, Sequence

from core.error_correction.models import (
    GAIAErrorCategory,
    GAIAErrorFinding,
    GAIASeverity,
)
from core.error_correction.canon_checker import CanonChecker
from core.logger import get_logger

_logger = get_logger("gaia.error_correction.detector")


class ErrorDetector:
    """
    Runs all configured detection tools and yields GAIAErrorFinding instances.

    Usage
    -----
    detector = ErrorDetector(repo_root=Path("."))
    findings = list(detector.run())

    # Chained convenience calls reuse the cached run() result:
    blocking = detector.blocking_findings()
    by_file  = detector.findings_by_file()

    # Force a fresh scan (e.g. after auto-repair):
    detector.invalidate_cache()
    findings = detector.run()
    """

    def __init__(
        self,
        repo_root: Optional[Path] = None,
        files: Optional[Sequence[str]] = None,
        skip_canon: bool = False,
    ) -> None:
        """
        Parameters
        ----------
        repo_root  : Root of the repository. Defaults to cwd.
        files      : Optional list of specific files to check.
                     When None, the entire repo_root is scanned.
        skip_canon : Set True to skip the CanonChecker (Ruff only).
        """
        self.repo_root  = repo_root or Path(".")
        self.files      = list(files) if files else None
        self.skip_canon = skip_canon
        self._cached_findings: Optional[list[GAIAErrorFinding]] = None

    # ---------------------------------------------------------------- #
    #  Public API                                                       #
    # ---------------------------------------------------------------- #

    def run(self) -> list[GAIAErrorFinding]:
        """Run all detectors and return a sorted list of findings.

        Results are cached after the first call. Subsequent calls return
        the cached list without re-invoking Ruff or CanonChecker.
        Call invalidate_cache() to force a fresh scan.
        """
        if self._cached_findings is not None:
            return self._cached_findings

        findings: list[GAIAErrorFinding] = []

        # 1. Ruff
        ruff_findings = self._run_ruff()
        findings.extend(ruff_findings)
        _logger.info(f"Ruff: {len(ruff_findings)} finding(s)")

        # 2. Canon Rule Checker
        if not self.skip_canon:
            canon_findings = self._run_canon_checker()
            findings.extend(canon_findings)
            _logger.info(f"CanonChecker: {len(canon_findings)} finding(s)")

        # Phase 1c stubs (future):
        # findings.extend(self._run_copyright_check())

        # Sort: severity first, then file, then line
        severity_order = {s: i for i, s in enumerate(GAIASeverity)}
        findings.sort(
            key=lambda f: (
                severity_order.get(f.severity, 99),
                f.file_path,
                f.line or 0,
            )
        )

        _logger.info(
            f"ErrorDetector: {len(findings)} total finding(s) across "
            f"{len({f.file_path for f in findings})} file(s) | "
            f"blocking={sum(1 for f in findings if f.is_blocking())}"
        )

        self._cached_findings = findings
        return self._cached_findings

    def invalidate_cache(self) -> None:
        """Clear the cached run() result so the next call performs a fresh scan."""
        self._cached_findings = None

    def iter(self) -> Iterator[GAIAErrorFinding]:
        """Streaming variant — yields findings as each detector completes.

        Note: does NOT use the cache — always performs a live scan.
        Use run() when you need cached/repeatable results.
        """
        yield from self._run_ruff()
        if not self.skip_canon:
            yield from self._run_canon_checker()

    # ---------------------------------------------------------------- #
    #  Ruff detector                                                    #
    # ---------------------------------------------------------------- #

    def _run_ruff(self) -> list[GAIAErrorFinding]:
        """Run `ruff check --output-format json --no-fix` and parse diagnostics."""
        cmd = [
            sys.executable, "-m", "ruff", "check",
            "--output-format", "json",
            "--no-fix",
        ]
        if self.files:
            cmd.extend(self.files)
        else:
            cmd.append(str(self.repo_root))

        _logger.debug(f"Running ruff: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.repo_root,
            )
        except FileNotFoundError:
            _logger.error("ruff not found — install with: pip install ruff")
            return []

        raw = result.stdout.strip()
        if not raw:
            return []

        try:
            diagnostics: list[dict] = json.loads(raw)
        except json.JSONDecodeError as exc:
            _logger.error(f"Failed to parse ruff JSON output: {exc}")
            return []

        findings = []
        for diag in diagnostics:
            file_path = diag.get("filename", "unknown")
            try:
                file_path = str(
                    Path(file_path).relative_to(self.repo_root.resolve())
                )
            except ValueError:
                pass
            findings.append(
                GAIAErrorFinding.from_ruff_diagnostic(diag, file_path)
            )
        return findings

    # ---------------------------------------------------------------- #
    #  Canon Rule Checker                                               #
    # ---------------------------------------------------------------- #

    def _run_canon_checker(self) -> list[GAIAErrorFinding]:
        """Run the GAIA CanonChecker and return findings."""
        checker = CanonChecker(
            repo_root=self.repo_root,
            paths=self.files,
        )
        return checker.run()

    # ---------------------------------------------------------------- #
    #  Convenience methods (all use cached run())                      #
    # ---------------------------------------------------------------- #

    def blocking_findings(self) -> list[GAIAErrorFinding]:
        """Return only CRITICAL and HIGH severity findings."""
        return [f for f in self.run() if f.is_blocking()]

    def findings_by_file(self) -> dict[str, list[GAIAErrorFinding]]:
        """Group all findings by file path."""
        result: dict[str, list[GAIAErrorFinding]] = {}
        for finding in self.run():
            result.setdefault(finding.file_path, []).append(finding)
        return result

    def findings_by_source(self) -> dict[str, list[GAIAErrorFinding]]:
        """Group all findings by source tool (ruff, gaia.canon_checker, etc.)."""
        result: dict[str, list[GAIAErrorFinding]] = {}
        for finding in self.run():
            result.setdefault(finding.source, []).append(finding)
        return result
