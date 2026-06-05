"""
gaia/cli.py
~~~~~~~~~~~
GAIA command-line interface.

Subcommands
-----------
  gaia start           Boot a GAIA session: initialise the RAG pipeline,
                       ingest Canon (warm or cold start), then launch the
                       FastAPI server via uvicorn.
  gaia status          Print Canon index and RAG pipeline status to stdout.
  gaia ingest-canon    Manually trigger Canon ingestion.
  gaia doctor          Environment health check.

Usage examples
--------------
  gaia start
  gaia start --ref main --store ~/.gaia/data --no-server
  gaia status
  gaia ingest-canon --force
  gaia ingest-canon --ref main --store /tmp/gaia-test
  gaia doctor

Installation
------------
Registered as a console_scripts entry point in pyproject.toml:
  [project.scripts]
  gaia = "gaia.cli:main"

After `pip install -e .` the `gaia` command is available on PATH.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Logging: plain INFO to stdout by default, DEBUG via GAIA_LOG_LEVEL=DEBUG
# ---------------------------------------------------------------------------
_LOG_LEVEL = os.environ.get("GAIA_LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=_LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("gaia.cli")

# ---------------------------------------------------------------------------
# ANSI colours (disabled when NO_COLOR env var is set or stdout is not a TTY)
# ---------------------------------------------------------------------------
_USE_COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ


def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text


GREEN  = "32"
YELLOW = "33"
CYAN   = "36"
BOLD   = "1"
RED    = "31"
DIM    = "2"


# ---------------------------------------------------------------------------
# Banner
# ---------------------------------------------------------------------------

_BANNER = r"""
  ██████╗  █████╗ ██╗ █████╗
 ██╔════╝ ██╔══██╗██║██╔══██╗
 ██║  ███╗███████║██║███████║
 ██║   ██║██╔══██║██║██╔══██║
 ╚██████╔╝██║  ██║██║██║  ██║
  ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝
  Sentient Quantum-Intelligent OS
"""


def _print_banner() -> None:
    print(_c(_BANNER, CYAN))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _default_store() -> Path:
    return Path.home() / ".gaia" / "data"


def _build_rag(store: Optional[Path] = None) -> object:
    """
    Import and return a RAGPipeline instance.
    Returns None with a warning if the module is unavailable.
    """
    try:
        from core.rag.pipeline import RAGPipeline
        return RAGPipeline()
    except ImportError as exc:
        logger.warning("RAGPipeline not available: %s", exc)
        return None


def _print_table(rows: list[tuple[str, str]]) -> None:
    """Print a simple two-column key/value table."""
    if not rows:
        return
    key_width = max(len(r[0]) for r in rows) + 2
    for key, val in rows:
        print(f"  {_c(key.ljust(key_width), BOLD)} {val}")


def _bool_icon(val: object) -> str:
    if val is True:
        return _c("✓", GREEN)
    if val is False:
        return _c("✗", RED)
    return str(val)


# ---------------------------------------------------------------------------
# Subcommand: start
# ---------------------------------------------------------------------------

def cmd_start(args: argparse.Namespace) -> int:
    """
    Boot GAIA:
    1. Print banner.
    2. Initialise RAG pipeline.
    3. Ingest Canon (warm or cold start).
    4. Print startup report.
    5. Launch uvicorn (unless --no-server).
    """
    _print_banner()
    print(_c("► Awakening GAIA...", CYAN))
    print()

    store_path: Optional[Path] = None if args.no_store else (
        Path(args.store) if args.store else _default_store()
    )

    # --- RAG init ---
    rag = _build_rag()
    if rag is None:
        print(_c("  [WARN] RAG pipeline unavailable — Canon context disabled.", YELLOW))
    else:
        print(_c("  RAG pipeline initialised.", GREEN))

    # --- Canon ingestion ---
    if rag is not None:
        print()
        print(_c("► Consulting the Canon...", CYAN))
        t0 = time.monotonic()
        try:
            report = rag.ingest_canon(
                ref=args.ref,
                force=args.force,
                store_path=store_path,
            )
            elapsed = time.monotonic() - t0
            status  = report.get("status", "unknown")
            warm    = report.get("warm_start", False)
            docs    = report.get("doc_count", 0)
            chunks  = report.get("chunk_count", 0)
            fp      = report.get("fingerprint") or "—"
            store_s = report.get("store_path") or "memory"

            if status in ("ok", "warm_start"):
                icon = _c("✓", GREEN)
                mode = _c("warm start", GREEN) if warm else _c("cold start", YELLOW)
                print(f"  {icon} Canon loaded  [{mode}]")
                print()
                _print_table([
                    ("Documents",   str(docs)),
                    ("Chunks",       str(chunks)),
                    ("Duration",     f"{elapsed:.2f}s"),
                    ("Fingerprint",  fp),
                    ("Index path",   store_s),
                ])
            elif status == "already_loaded":
                print(f"  {_c('✓', GREEN)} Canon already loaded — skipping.")
            else:
                print(_c(f"  [WARN] Canon ingestion status: {status}", YELLOW))
        except Exception as exc:  # noqa: BLE001
            print(_c(f"  [ERROR] Canon ingestion failed: {exc}", RED))

    print()

    # --- Launch server ---
    if args.no_server:
        print(_c("  --no-server set. Skipping uvicorn launch.", DIM))
        print(_c("  GAIA is ready.", GREEN))
        return 0

    host = os.environ.get("GAIA_HOST", "0.0.0.0")
    port = int(os.environ.get("GAIA_PORT", "8000"))
    workers = int(os.environ.get("GAIA_WORKERS", "1"))

    print(_c(f"► Launching API server on {host}:{port} (workers={workers})...", CYAN))
    print()

    try:
        import uvicorn
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            workers=workers,
            log_level=_LOG_LEVEL.lower(),
        )
    except ImportError:
        print(_c("  [ERROR] uvicorn not installed. Run: pip install uvicorn", RED))
        return 1
    except Exception as exc:  # noqa: BLE001
        print(_c(f"  [ERROR] Server launch failed: {exc}", RED))
        return 1

    return 0


# ---------------------------------------------------------------------------
# Subcommand: status
# ---------------------------------------------------------------------------

def cmd_status(args: argparse.Namespace) -> int:
    """
    Print Canon index and RAG pipeline status.
    """
    _print_banner()
    print(_c("► GAIA Status", CYAN))
    print()

    rag = _build_rag()
    if rag is None:
        print(_c("  RAG pipeline unavailable.", RED))
        return 1

    store_path = Path(args.store) if args.store else _default_store()

    # Check persistent index state without ingesting
    try:
        from core.rag.index_store import IndexStore
        store = IndexStore(data_dir=store_path)
        db_exists  = store.db_exists()
        stored_fp  = store.read_fingerprint() or "—"
        db_path_s  = str(store.db_path)
        db_size_kb = (
            round(store.db_path.stat().st_size / 1024, 1)
            if db_exists else 0
        )
    except Exception:  # noqa: BLE001
        db_exists = False
        stored_fp = "—"
        db_path_s = str(store_path / "canon_index.db")
        db_size_kb = 0

    print(_c("  Canon Index", BOLD))
    _print_table([
        ("DB path",      db_path_s),
        ("DB exists",    _bool_icon(db_exists)),
        ("DB size",      f"{db_size_kb} KB" if db_exists else "—"),
        ("Fingerprint",  stored_fp[:16] if stored_fp != "—" else "—"),
    ])
    print()

    # If --json flag, emit machine-readable output
    if getattr(args, "json", False):
        out = {
            "db_path": db_path_s,
            "db_exists": db_exists,
            "db_size_kb": db_size_kb,
            "fingerprint": stored_fp,
        }
        print(json.dumps(out, indent=2))

    return 0


# ---------------------------------------------------------------------------
# Subcommand: ingest-canon
# ---------------------------------------------------------------------------

def cmd_ingest_canon(args: argparse.Namespace) -> int:
    """
    Manually trigger Canon ingestion.
    """
    _print_banner()
    force_s = _c(" (forced)", YELLOW) if args.force else ""
    print(_c(f"► Canon Ingestion{force_s}", CYAN))
    print()

    rag = _build_rag()
    if rag is None:
        print(_c("  [ERROR] RAG pipeline unavailable.", RED))
        return 1

    store_path: Optional[Path] = None if args.no_store else (
        Path(args.store) if args.store else _default_store()
    )

    t0 = time.monotonic()
    try:
        report = rag.ingest_canon(
            ref=args.ref,
            force=args.force,
            store_path=store_path,
        )
    except Exception as exc:  # noqa: BLE001
        print(_c(f"  [ERROR] {exc}", RED))
        return 1

    elapsed = time.monotonic() - t0
    status  = report.get("status", "unknown")
    warm    = report.get("warm_start", False)
    docs    = report.get("doc_count", 0)
    chunks  = report.get("chunk_count", 0)
    fp      = report.get("fingerprint") or "—"
    store_s = report.get("store_path") or "memory"

    if status in ("ok", "warm_start"):
        mode = _c("warm start", GREEN) if warm else _c("cold start", YELLOW)
        print(f"  {_c('✓', GREEN)} Done [{mode}]")
    elif status == "already_loaded":
        print(f"  {_c('✓', GREEN)} Already loaded — use --force to rebuild.")
    else:
        print(_c(f"  [WARN] Status: {status}", YELLOW))

    print()
    _print_table([
        ("Status",      status),
        ("Documents",   str(docs)),
        ("Chunks",       str(chunks)),
        ("Duration",     f"{elapsed:.2f}s"),
        ("Fingerprint",  fp),
        ("Index path",   store_s),
    ])
    print()

    if getattr(args, "json", False):
        print(json.dumps({**report, "elapsed_s": round(elapsed, 3)}, indent=2))

    return 0 if status in ("ok", "warm_start", "already_loaded") else 1


# ---------------------------------------------------------------------------
# Subcommand: doctor
# ---------------------------------------------------------------------------

def cmd_doctor(args: argparse.Namespace) -> int:
    """
    Environment health check.
    Reports: Python version, required imports, data dir writability,
    fingerprint file integrity.
    """
    _print_banner()
    print(_c("► GAIA Doctor", CYAN))
    print()

    issues: list[str] = []

    # Python version
    ver = sys.version_info
    ver_s = f"{ver.major}.{ver.minor}.{ver.micro}"
    ok = ver >= (3, 11)
    rows = [("Python", f"{ver_s}  {_bool_icon(ok)}")]
    if not ok:
        issues.append(f"Python >=3.11 required (got {ver_s})")

    # Key imports
    _imports = [
        ("core.rag.pipeline",    "RAGPipeline"),
        ("core.rag.canon_loader","CanonLoader"),
        ("core.rag.index_store", "IndexStore"),
        ("core.agentic_loop",    "AgenticLoop"),
        ("fastapi",              "FastAPI"),
        ("uvicorn",              "uvicorn"),
        ("httpx",                "httpx"),
        ("numpy",                "numpy"),
    ]
    for mod, label in _imports:
        try:
            __import__(mod)
            rows.append((label, _bool_icon(True)))
        except ImportError as exc:
            rows.append((label, _c(f"✗  {exc}", RED)))
            issues.append(f"{label}: {exc}")

    # Data dir
    store_path = Path(args.store) if args.store else _default_store()
    try:
        store_path.mkdir(parents=True, exist_ok=True)
        test_file = store_path / ".gaia_write_test"
        test_file.write_text("ok")
        test_file.unlink()
        rows.append(("Data dir writable", _bool_icon(True)))
    except Exception as exc:  # noqa: BLE001
        rows.append(("Data dir writable", _c(f"✗  {exc}", RED)))
        issues.append(f"Data dir not writable: {exc}")

    # Fingerprint integrity
    try:
        from core.rag.index_store import IndexStore
        store = IndexStore(data_dir=store_path)
        fp = store.read_fingerprint()
        if fp is None:
            rows.append(("Fingerprint", _c("absent (cold start required)", YELLOW)))
        elif len(fp) == 64 and all(c in "0123456789abcdef" for c in fp):
            rows.append(("Fingerprint", _c(f"valid ({fp[:16]}…)", GREEN)))
        else:
            rows.append(("Fingerprint", _c(f"malformed: {fp[:32]}", RED)))
            issues.append("Fingerprint file is malformed")
    except Exception as exc:  # noqa: BLE001
        rows.append(("Fingerprint", _c(f"error: {exc}", RED)))

    _print_table(rows)
    print()

    if issues:
        print(_c(f"  {len(issues)} issue(s) found:", YELLOW))
        for i in issues:
            print(_c(f"    • {i}", YELLOW))
        print()
        return 1
    else:
        print(_c("  All checks passed. GAIA is healthy.", GREEN))
        return 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="gaia",
        description="GAIA-OS command-line interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  gaia start                        # boot with Canon, launch server\n"
            "  gaia start --no-server            # boot Canon only, no server\n"
            "  gaia start --force                # force Canon re-embed\n"
            "  gaia ingest-canon --force         # rebuild Canon index\n"
            "  gaia ingest-canon --ref main      # ingest from main branch\n"
            "  gaia status                       # show index state\n"
            "  gaia status --json                # machine-readable output\n"
            "  gaia doctor                       # environment health check\n"
        ),
    )

    # Global flags
    parser.add_argument(
        "--log-level",
        default=os.environ.get("GAIA_LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log verbosity (default: INFO)",
    )

    subs = parser.add_subparsers(dest="command", metavar="<command>")
    subs.required = True

    # ------------------------------------------------------------------
    # start
    # ------------------------------------------------------------------
    p_start = subs.add_parser("start", help="Boot GAIA and launch the API server")
    p_start.add_argument(
        "--ref",
        default="feat/obs-rag",
        help="Git ref to load Canon from (default: feat/obs-rag)",
    )
    p_start.add_argument(
        "--store",
        default=None,
        metavar="PATH",
        help=f"Canon index directory (default: {_default_store()})",
    )
    p_start.add_argument(
        "--no-store",
        action="store_true",
        help="Disable persistence — use in-memory index only",
    )
    p_start.add_argument(
        "--force",
        action="store_true",
        help="Force Canon re-embed even if fingerprint matches",
    )
    p_start.add_argument(
        "--no-server",
        action="store_true",
        help="Initialise Canon but do not launch the API server",
    )
    p_start.set_defaults(func=cmd_start)

    # ------------------------------------------------------------------
    # status
    # ------------------------------------------------------------------
    p_status = subs.add_parser("status", help="Print Canon index and pipeline status")
    p_status.add_argument(
        "--store",
        default=None,
        metavar="PATH",
        help="Canon index directory to inspect",
    )
    p_status.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON to stdout",
    )
    p_status.set_defaults(func=cmd_status)

    # ------------------------------------------------------------------
    # ingest-canon
    # ------------------------------------------------------------------
    p_ingest = subs.add_parser("ingest-canon", help="Manually trigger Canon ingestion")
    p_ingest.add_argument(
        "--ref",
        default="feat/obs-rag",
        help="Git ref to load Canon from",
    )
    p_ingest.add_argument(
        "--store",
        default=None,
        metavar="PATH",
        help="Canon index directory",
    )
    p_ingest.add_argument(
        "--no-store",
        action="store_true",
        help="In-memory only (no SQLite write)",
    )
    p_ingest.add_argument(
        "--force",
        action="store_true",
        help="Delete existing index and rebuild from scratch",
    )
    p_ingest.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON report",
    )
    p_ingest.set_defaults(func=cmd_ingest_canon)

    # ------------------------------------------------------------------
    # doctor
    # ------------------------------------------------------------------
    p_doctor = subs.add_parser("doctor", help="Run environment health checks")
    p_doctor.add_argument(
        "--store",
        default=None,
        metavar="PATH",
        help="Data directory to check for writability",
    )
    p_doctor.set_defaults(func=cmd_doctor)

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: Optional[list[str]] = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    # Apply log level from flag
    logging.getLogger().setLevel(args.log_level.upper())

    rc = args.func(args)
    sys.exit(rc or 0)


if __name__ == "__main__":
    main()
