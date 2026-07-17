# Copyright (c) 2026 R0GV3 The Alchemist
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
core/error_correction/reporter.py

GAIA Error Correction — Artifact Reporter (Phase 1)

Consumes a list of GAIAErrorFinding instances and writes:
  1. A human-readable Markdown report  (error_report.md)
  2. A machine-readable JSON artifact  (error_report.json)

Both files include:
  - Run metadata (timestamp, repo, total counts)
  - Severity breakdown
  - Per-file finding tables
  - Provenance metadata for the Provenance Layer (Issue #753)

Canon Ref: C01, C30, Issue #755 Phase 1
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Sequence

from core.error_correction import __version__ as _EC_VERSION
from core.error_correction.models import GAIAErrorFinding, GAIASeverity
from core.logger import get_logger

_logger = get_logger("gaia.error_correction.reporter")

_SEVERITY_EMOJI = {
    GAIASeverity.CRITICAL: "🔴",
    GAIASeverity.HIGH:     "🟠",
    GAIASeverity.MEDIUM:   "🟡",
    GAIASeverity.LOW:      "🔵",
    GAIASeverity.INFO:     "⚪",
}


class ErrorReporter:
    """
    Writes Markdown and JSON error reports from a list of GAIAErrorFinding.

    Usage
    -----
    reporter = ErrorReporter(output_dir=Path("reports"))
    reporter.write(findings)
    """

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        repo_name: str = "GAIA",
    ) -> None:
        self.output_dir = output_dir or Path("reports")
        self.repo_name  = repo_name
        self.output_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------------- #
    #  Public API                                                       #
    # ---------------------------------------------------------------- #

    def write(self, findings: Sequence[GAIAErrorFinding]) -> dict[str, Path]:
        """
        Write both report formats and return paths.

        Returns
        -------
        {"markdown": Path, "json": Path}
        """
        findings = list(findings)
        run_meta = self._run_metadata(findings)

        md_path   = self._write_markdown(findings, run_meta)
        json_path = self._write_json(findings, run_meta)

        _logger.info(
            f"ErrorReporter: wrote reports to {self.output_dir} "
            f"({len(findings)} finding(s))"
        )
        return {"markdown": md_path, "json": json_path}

    # ---------------------------------------------------------------- #
    #  Metadata                                                         #
    # ---------------------------------------------------------------- #

    def _run_metadata(self, findings: list[GAIAErrorFinding]) -> dict:
        counts = {s.value: 0 for s in GAIASeverity}
        for f in findings:
            counts[f.severity.value] += 1

        blocking = sum(1 for f in findings if f.is_blocking())
        files    = len({f.file_path for f in findings})

        return {
            "repo":            self.repo_name,
            "generated_at":   datetime.now(timezone.utc).isoformat(),
            "total_findings": len(findings),
            "blocking":       blocking,
            "files_affected": files,
            "severity_counts": counts,
            "provenance": {
                "tool":    "gaia.error_correction.reporter",
                "version": _EC_VERSION,
            },
        }

    # ---------------------------------------------------------------- #
    #  Markdown report                                                  #
    # ---------------------------------------------------------------- #

    def _write_markdown(self, findings: list[GAIAErrorFinding], meta: dict) -> Path:
        lines: list[str] = []
        s = meta["severity_counts"]

        lines += [
            f"# 🔍 GAIA Error Correction Report",
            f"",
            f"**Repo:** `{meta['repo']}`  ",
            f"**Generated:** {meta['generated_at']}  ",
            f"**Total findings:** {meta['total_findings']}  ",
            f"**Blocking (CRITICAL + HIGH):** {meta['blocking']}  ",
            f"**Files affected:** {meta['files_affected']}  ",
            f"",
            f"## Severity Breakdown",
            f"",
            f"| Severity | Count |",
            f"|----------|-------|" ,
        ]
        for sev in GAIASeverity:
            emoji = _SEVERITY_EMOJI[sev]
            lines.append(f"| {emoji} {sev.value.capitalize()} | {s[sev.value]} |")

        # Group by file
        by_file: dict[str, list[GAIAErrorFinding]] = {}
        for f in findings:
            by_file.setdefault(f.file_path, []).append(f)

        if by_file:
            lines += ["", "## Findings by File", ""]
            for file_path, file_findings in sorted(by_file.items()):
                lines += [
                    f"### `{file_path}`",
                    f"",
                    f"| # | Severity | Rule | Location | Message | Fix? |",
                    f"|---|----------|------|----------|---------|------|",
                ]
                for i, f in enumerate(file_findings, 1):
                    emoji   = _SEVERITY_EMOJI[f.severity]
                    fix_str = "✅" if f.fix_available else "➖"
                    loc     = f.location_str().split(":", 1)[1] if ":" in f.location_str() else "—"
                    lines.append(
                        f"| {i} | {emoji} {f.severity.value} "
                        f"| `{f.rule_id}` | {loc} "
                        f"| {f.message} | {fix_str} |"
                    )
                lines.append("")
        else:
            lines += ["", "✅ No findings. Codebase is clean.", ""]

        lines += [
            "---",
            f"*Generated by GAIA Error Correction Engine v{_EC_VERSION} — Phase 1*  ",
            f"*Canon Ref: C01, C30, Issue #755*",
        ]

        path = self.output_dir / "error_report.md"
        path.write_text("\n".join(lines), encoding="utf-8")
        return path

    # ---------------------------------------------------------------- #
    #  JSON artifact                                                    #
    # ---------------------------------------------------------------- #

    def _write_json(self, findings: list[GAIAErrorFinding], meta: dict) -> Path:
        payload = {
            "meta":     meta,
            "findings": [f.to_dict() for f in findings],
        }
        path = self.output_dir / "error_report.json"
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return path
