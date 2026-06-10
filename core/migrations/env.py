"""
core/migrations/env.py
======================
Lightweight Alembic-style migration runner for GAIA-OS SQLite databases.

Usage (CLI):
    python core/migrations/env.py                   # apply all pending
    python core/migrations/env.py --dry-run         # preview only
    python core/migrations/env.py --db memory       # memory DB only
    python core/migrations/env.py --db ledger       # ledger DB only
    python core/migrations/env.py \\
        --memory-path /data/gaia_memory.db \\
        --ledger-path /data/gaia_audit.db

Usage (programmatic — called by server on startup):
    from core.migrations.env import apply_all
    apply_all()  # uses default paths
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import shutil
import sqlite3
import time
from pathlib import Path

log = logging.getLogger("gaia.migrations")

_REPO_ROOT    = Path(__file__).resolve().parents[2]
_DEFAULT_MEMORY_DB = _REPO_ROOT / "data" / "gaia_memory.db"
_DEFAULT_LEDGER_DB = _REPO_ROOT / "data" / "gaia_audit.db"
_BACKUP_DIR        = _REPO_ROOT / "data" / "backups"

_CREATE_VERSIONS = """
CREATE TABLE IF NOT EXISTS schema_versions (
    version    TEXT PRIMARY KEY,
    applied_at REAL NOT NULL,
    checksum   TEXT NOT NULL
);
"""


def _checksum(sql: str) -> str:
    return hashlib.sha256(sql.encode()).hexdigest()


def _backup(db_path: Path) -> None:
    """Copy the DB file to data/backups/ before any migration."""
    if not db_path.exists():
        return
    _BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp  = int(time.time())
    target = _BACKUP_DIR / f"{db_path.stem}_{stamp}.db"
    shutil.copy2(db_path, target)
    log.info("[migrations] backup written → %s", target)


def _applied_versions(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute("SELECT version FROM schema_versions").fetchall()
    return {r[0] for r in rows}


def _mark_applied(conn: sqlite3.Connection, version: str, checksum: str) -> None:
    conn.execute(
        "INSERT OR IGNORE INTO schema_versions (version, applied_at, checksum) VALUES (?,?,?)",
        (version, time.time(), checksum),
    )
    conn.commit()


def apply_migrations(
    db_path:   Path,
    sql_dir:   Path,
    dry_run:   bool = False,
) -> list[str]:
    """
    Apply all pending migrations in *sql_dir* to the SQLite database at *db_path*.

    Returns a list of version names that were applied (or would be applied
    in dry-run mode).
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(_CREATE_VERSIONS)
    conn.commit()

    applied = _applied_versions(conn)

    # Collect and sort migration files
    migrations = sorted(
        sql_dir.glob("V*.sql"),
        key=lambda p: p.stem,  # lexicographic order on V001__ prefix sorts correctly
    )

    pending = [m for m in migrations if m.stem not in applied]

    if not pending:
        log.info("[migrations] %s — already up to date.", db_path.name)
        conn.close()
        return []

    applied_this_run: list[str] = []

    if not dry_run:
        _backup(db_path)

    for mig in pending:
        sql      = mig.read_text(encoding="utf-8")
        checksum = _checksum(sql)
        log.info(
            "[migrations] %s %s %s",
            "[DRY RUN]" if dry_run else "Applying",
            db_path.name,
            mig.stem,
        )
        if not dry_run:
            try:
                # executescript commits implicitly
                conn.executescript(sql)
                _mark_applied(conn, mig.stem, checksum)
            except sqlite3.OperationalError as exc:
                log.error(
                    "[migrations] FAILED %s on %s: %s",
                    mig.stem, db_path.name, exc,
                )
                conn.close()
                raise
        applied_this_run.append(mig.stem)

    conn.close()
    return applied_this_run


def apply_all(
    memory_path: Path | None = None,
    ledger_path: Path | None = None,
    dry_run:     bool        = False,
) -> dict[str, list[str]]:
    """
    Apply all pending migrations to both databases.

    Called by the GAIA server on startup::

        from core.migrations.env import apply_all
        apply_all()

    Returns a dict {"memory": [...], "ledger": [...]} of applied versions.
    """
    here = Path(__file__).parent

    memory_applied = apply_migrations(
        db_path = memory_path or _DEFAULT_MEMORY_DB,
        sql_dir = here / "memory",
        dry_run = dry_run,
    )
    ledger_applied = apply_migrations(
        db_path = ledger_path or _DEFAULT_LEDGER_DB,
        sql_dir = here / "ledger",
        dry_run = dry_run,
    )
    return {"memory": memory_applied, "ledger": ledger_applied}


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level   = logging.INFO,
        format  = "%(asctime)s  %(levelname)-7s  %(message)s",
        datefmt = "%H:%M:%S",
    )

    parser = argparse.ArgumentParser(description="GAIA-OS SQL migration runner")
    parser.add_argument("--db",          choices=["memory", "ledger", "both"],
                        default="both",   help="Which database to migrate")
    parser.add_argument("--dry-run",     action="store_true",
                        help="Preview pending migrations without executing them")
    parser.add_argument("--memory-path", type=Path, default=None,
                        help="Override default memory DB path")
    parser.add_argument("--ledger-path", type=Path, default=None,
                        help="Override default ledger DB path")
    args = parser.parse_args()

    here = Path(__file__).parent

    if args.db in ("memory", "both"):
        apply_migrations(
            db_path = args.memory_path or _DEFAULT_MEMORY_DB,
            sql_dir = here / "memory",
            dry_run = args.dry_run,
        )
    if args.db in ("ledger", "both"):
        apply_migrations(
            db_path = args.ledger_path or _DEFAULT_LEDGER_DB,
            sql_dir = here / "ledger",
            dry_run = args.dry_run,
        )
