# Copyright (c) 2026 R0GV3 The Alchemist
# GAIA — The Global Autonomous Intelligence Architecture
# Licensed under the GAIA Sovereign License (see LICENSE.md)
"""
core/error_correction/canon_checker.py

GAIA Error Correction — Canon Rule Checker (Phase 1b)

Statically analyzes Python source files for violations of GAIA’s
architectural Canon rules. Every finding is a GAIAErrorFinding with
category=CANON_VIOLATION.

Enforced rules (Phase 1b)
--------------------------
  CANON-01  — C01 Sovereignty: every core/*.py module must declare a
               Canon Ref in its docstring or header comment.
  CANON-02  — C30 No Silent Failures: bare `except:` or `except Exception:`
               without a log/raise is forbidden.
  CANON-03  — C30 No Silent Failures: `pass` alone inside an except block
               is forbidden.
  CANON-04  — C01 Sovereignty: direct `print()` calls in core/*.py are
               forbidden — use get_logger().
  CANON-05  — C01 Sovereignty: `os.environ` accessed directly in core/*.py
               is forbidden outside config/settings modules — use
               GAIA’s settings layer.
  CANON-06  — C15 Consent: any file touching `user` data must not write
               PII to logs (naive heuristic: log calls containing
               `password`, `token`, `secret`, `api_key`).
  CANON-07  — C30 No Silent Failures: TODO / FIXME / HACK comments in
               core/*.py are flagged as INFO — unresolved technical debt.
  CANON-08  — C01 Sovereignty: wildcard imports (`from x import *`) in
               core/*.py are forbidden except in explicit re-export stubs.

Phase 2 rules (stubbed, not yet active):
  CANON-09  — C32 Synergy: cross-module import cycles detected via AST.
  CANON-10  — C01: every public function in core/*.py must have a docstring.

Canon Ref: C01, C15, C30, Issue #755 Phase 1b
"""
from __future__ import annotations

import ast
import re
import tokenize
import io
from pathlib import Path
from typing import Iterator, Sequence

from core.error_correction.models import (
    GAIAErrorCategory,
    GAIAErrorFinding,
    GAIASeverity,
)
from core.logger import get_logger

_logger = get_logger("gaia.error_correction.canon_checker")

# Regex to detect an existing Canon Ref annotation in header / docstring
_CANON_REF_RE = re.compile(
    r"Canon\s+Ref(?:erence)?[:\s]+[A-Z][0-9]+", re.IGNORECASE
)

# Patterns for PII leak heuristic (CANON-06)
_PII_PATTERNS = re.compile(
    r"(password|passwd|secret|api[_\-]?key|token|auth[_\-]?token)",
    re.IGNORECASE,
)

# Config/settings modules exempt from CANON-05
_SETTINGS_EXEMPT = re.compile(
    r"(config|settings|env|environment)[.\/]",
    re.IGNORECASE,
)


class CanonChecker:
    """
    Runs Canon architectural rule checks on Python source files.

    Usage
    -----
    checker = CanonChecker(repo_root=Path("."))
    findings = checker.run()
    """

    def __init__(
        self,
        repo_root: Path | None = None,
        paths: Sequence[str] | None = None,
    ) -> None:
        """
        Parameters
        ----------
        repo_root : Root of the repository. Defaults to cwd.
        paths     : Explicit list of file paths to check.
                    When None, all core/*.py files are scanned.
        """
        self.repo_root = (repo_root or Path(".")).resolve()
        self._paths = list(paths) if paths else None

    # ---------------------------------------------------------------- #
    #  Public API                                                       #
    # ---------------------------------------------------------------- #

    def run(self) -> list[GAIAErrorFinding]:
        """Run all Canon checks and return findings sorted by severity."""
        findings: list[GAIAErrorFinding] = []
        for path in self._target_files():
            findings.extend(self._check_file(path))
        findings.sort(
            key=lambda f: (
                list(GAIASeverity).index(f.severity),
                f.file_path,
                f.line or 0,
            )
        )
        _logger.info(
            f"CanonChecker: {len(findings)} Canon finding(s) in "
            f"{len({f.file_path for f in findings})} file(s)"
        )
        return findings

    # ---------------------------------------------------------------- #
    #  File collection                                                  #
    # ---------------------------------------------------------------- #

    def _target_files(self) -> Iterator[Path]:
        """Yield Python files to check."""
        if self._paths:
            for p in self._paths:
                yield Path(p)
            return

        # Default: scan core/, api/, server.py at repo root
        scan_dirs = ["core", "api"]
        for d in scan_dirs:
            target = self.repo_root / d
            if target.is_dir():
                yield from target.rglob("*.py")
        # top-level server.py
        server = self.repo_root / "server.py"
        if server.exists():
            yield server

    # ---------------------------------------------------------------- #
    #  Per-file checks                                                  #
    # ---------------------------------------------------------------- #

    def _check_file(self, path: Path) -> list[GAIAErrorFinding]:
        """Run all Canon checks on a single file."""
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            _logger.warning(f"CanonChecker: cannot read {path}: {exc}")
            return []

        # Make path repo-relative for display
        try:
            rel = str(path.relative_to(self.repo_root))
        except ValueError:
            rel = str(path)

        findings: list[GAIAErrorFinding] = []

        # Parse AST (best-effort — skip unparseable files)
        tree: ast.Module | None = None
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            pass  # syntax errors are Ruff’s domain; we skip AST checks

        # Run each rule
        findings.extend(self._canon01_canon_ref_present(source, rel))
        if tree:
            findings.extend(self._canon02_bare_except(tree, rel))
            findings.extend(self._canon03_silent_pass(tree, rel))
            findings.extend(self._canon04_no_print(tree, rel))
            findings.extend(self._canon05_no_raw_environ(tree, rel))
            findings.extend(self._canon08_no_wildcard_import(tree, rel, source))
        findings.extend(self._canon06_pii_in_logs(source, rel))
        findings.extend(self._canon07_tech_debt(source, rel))

        return findings

    # ---------------------------------------------------------------- #
    #  CANON-01: Canon Ref present in core modules                     #
    # ---------------------------------------------------------------- #

    def _canon01_canon_ref_present(
        self, source: str, rel: str
    ) -> list[GAIAErrorFinding]:
        # Only enforce on core/ modules (not tests, migrations, stubs)
        if not rel.startswith("core/"):
            return []
        if "test" in rel or "migration" in rel or "__pycache__" in rel:
            return []
        # Check first 40 lines for a Canon Ref annotation
        header = "\n".join(source.splitlines()[:40])
        if not _CANON_REF_RE.search(header):
            return [self._finding(
                rule_id="CANON-01",
                message=(
                    "Missing Canon Ref annotation. Every core/ module must "
                    "declare its Canon references (e.g. 'Canon Ref: C01') "
                    "in the first 40 lines. (C01 Sovereignty)"
                ),
                file_path=rel,
                severity=GAIASeverity.MEDIUM,
                line=1,
            )]
        return []

    # ---------------------------------------------------------------- #
    #  CANON-02: No bare except without log/raise                      #
    # ---------------------------------------------------------------- #

    def _canon02_bare_except(
        self, tree: ast.Module, rel: str
    ) -> list[GAIAErrorFinding]:
        findings = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            # Bare `except:` or `except Exception:` (no alias)
            is_bare = node.type is None
            is_broad = (
                node.type is not None
                and isinstance(node.type, ast.Name)
                and node.type.id in ("Exception", "BaseException")
                and node.name is None  # no `as e` binding
            )
            if not (is_bare or is_broad):
                continue
            # Check if body contains a log call or re-raise
            body_src = ast.unparse(node) if hasattr(ast, "unparse") else ""
            has_log   = any(k in body_src for k in ("_logger", "logging", "log.", "logger."))
            has_raise = any(isinstance(n, ast.Raise) for n in ast.walk(node))
            if not (has_log or has_raise):
                findings.append(self._finding(
                    rule_id="CANON-02",
                    message=(
                        "Bare/broad except without log or re-raise swallows "
                        "errors silently. Add logging or re-raise. (C30 No Silent Failures)"
                    ),
                    file_path=rel,
                    severity=GAIASeverity.HIGH,
                    line=getattr(node, "lineno", None),
                ))
        return findings

    # ---------------------------------------------------------------- #
    #  CANON-03: No silent pass in except                              #
    # ---------------------------------------------------------------- #

    def _canon03_silent_pass(
        self, tree: ast.Module, rel: str
    ) -> list[GAIAErrorFinding]:
        findings = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            # Body is exactly one `pass` statement
            if (
                len(node.body) == 1
                and isinstance(node.body[0], ast.Pass)
            ):
                findings.append(self._finding(
                    rule_id="CANON-03",
                    message=(
                        "`pass` as the sole statement in an except block silently "
                        "discards the error. Log it or re-raise. (C30 No Silent Failures)"
                    ),
                    file_path=rel,
                    severity=GAIASeverity.HIGH,
                    line=getattr(node, "lineno", None),
                ))
        return findings

    # ---------------------------------------------------------------- #
    #  CANON-04: No print() in core/                                   #
    # ---------------------------------------------------------------- #

    def _canon04_no_print(
        self, tree: ast.Module, rel: str
    ) -> list[GAIAErrorFinding]:
        if not rel.startswith("core/"):
            return []
        # Exempt: __init__.py re-export stubs, scripts/
        if "script" in rel or rel.endswith("__init__.py"):
            return []
        findings = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Name) and func.id == "print":
                findings.append(self._finding(
                    rule_id="CANON-04",
                    message=(
                        "Direct print() call in core/ module. Use get_logger() "
                        "instead. (C01 Sovereignty — no uncontrolled output)"
                    ),
                    file_path=rel,
                    severity=GAIASeverity.MEDIUM,
                    line=getattr(node, "lineno", None),
                ))
        return findings

    # ---------------------------------------------------------------- #
    #  CANON-05: No raw os.environ in core/                            #
    # ---------------------------------------------------------------- #

    def _canon05_no_raw_environ(
        self, tree: ast.Module, rel: str
    ) -> list[GAIAErrorFinding]:
        if not rel.startswith("core/"):
            return []
        if _SETTINGS_EXEMPT.search(rel):
            return []
        findings = []
        for node in ast.walk(tree):
            # os.environ or os.getenv
            if isinstance(node, ast.Attribute):
                if (
                    isinstance(node.value, ast.Name)
                    and node.value.id == "os"
                    and node.attr in ("environ", "getenv")
                ):
                    findings.append(self._finding(
                        rule_id="CANON-05",
                        message=(
                            "Direct os.environ / os.getenv access in core/ module. "
                            "Use GAIA’s settings layer (core/config/ or core/settings.py). "
                            "(C01 Sovereignty)"
                        ),
                        file_path=rel,
                        severity=GAIASeverity.MEDIUM,
                        line=getattr(node, "lineno", None),
                    ))
        return findings

    # ---------------------------------------------------------------- #
    #  CANON-06: No PII in log calls                                   #
    # ---------------------------------------------------------------- #

    def _canon06_pii_in_logs(
        self, source: str, rel: str
    ) -> list[GAIAErrorFinding]:
        findings = []
        lines = source.splitlines()
        log_call_re = re.compile(
            r"(?:_logger|logger|logging)\.[a-z]+\s*\(", re.IGNORECASE
        )
        for i, line in enumerate(lines, 1):
            if log_call_re.search(line) and _PII_PATTERNS.search(line):
                findings.append(self._finding(
                    rule_id="CANON-06",
                    message=(
                        "Possible PII field name in log call "
                        f"({_PII_PATTERNS.search(line).group()}). "
                        "Never log raw credentials or secrets. (C15 Consent)"
                    ),
                    file_path=rel,
                    severity=GAIASeverity.CRITICAL,
                    line=i,
                ))
        return findings

    # ---------------------------------------------------------------- #
    #  CANON-07: Tech debt comments                                    #
    # ---------------------------------------------------------------- #

    def _canon07_tech_debt(
        self, source: str, rel: str
    ) -> list[GAIAErrorFinding]:
        if not rel.startswith("core/"):
            return []
        debt_re = re.compile(r"#.*(TODO|FIXME|HACK|XXX)", re.IGNORECASE)
        findings = []
        for i, line in enumerate(source.splitlines(), 1):
            m = debt_re.search(line)
            if m:
                tag = m.group(1).upper()
                findings.append(self._finding(
                    rule_id="CANON-07",
                    message=(
                        f"{tag} comment indicates unresolved technical debt. "
                        "Convert to a tracked GitHub issue and remove the comment. "
                        "(C30 No Silent Failures)"
                    ),
                    file_path=rel,
                    severity=GAIASeverity.LOW,
                    line=i,
                ))
        return findings

    # ---------------------------------------------------------------- #
    #  CANON-08: No wildcard imports in core/                          #
    # ---------------------------------------------------------------- #

    def _canon08_no_wildcard_import(
        self, tree: ast.Module, rel: str, source: str
    ) -> list[GAIAErrorFinding]:
        if not rel.startswith("core/"):
            return []
        # Re-export stubs explicitly suppress with noqa: F403
        if "noqa: F403" in source:
            return []
        findings = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name == "*":
                        findings.append(self._finding(
                            rule_id="CANON-08",
                            message=(
                                f"Wildcard import `from {node.module} import *` "
                                "in core/ module. Be explicit about what you import. "
                                "(C01 Sovereignty)"
                            ),
                            file_path=rel,
                            severity=GAIASeverity.MEDIUM,
                            line=getattr(node, "lineno", None),
                        ))
        return findings

    # ---------------------------------------------------------------- #
    #  Finding factory                                                  #
    # ---------------------------------------------------------------- #

    def _finding(
        self,
        rule_id: str,
        message: str,
        file_path: str,
        severity: GAIASeverity,
        line: int | None = None,
        col: int | None = None,
    ) -> GAIAErrorFinding:
        return GAIAErrorFinding(
            rule_id=rule_id,
            message=message,
            file_path=file_path,
            source="gaia.canon_checker",
            category=GAIAErrorCategory.CANON_VIOLATION,
            severity=severity,
            line=line,
            col=col,
            fix_available=False,
            confidence=0.9,
            provenance={
                "tool":    "gaia.canon_checker",
                "version": "1.0.0",
                "rule":    rule_id,
            },
        )
