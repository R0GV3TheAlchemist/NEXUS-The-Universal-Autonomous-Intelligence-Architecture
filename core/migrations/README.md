# GAIA-OS SQL Migrations

Versioned, idempotent DDL migrations for the two Phase 3 SQLite databases:

| Database | Default path | Migration folder |
|---|---|---|
| Memory store | `data/gaia_memory.db` | `core/migrations/memory/` |
| Audit ledger | `data/gaia_audit.db` | `core/migrations/ledger/` |

## Running migrations

```bash
# Apply all pending migrations to both databases (safe to re-run)
python core/migrations/env.py

# Apply to a specific database only
python core/migrations/env.py --db memory
python core/migrations/env.py --db ledger

# Dry-run: show what would be applied without executing
python core/migrations/env.py --dry-run

# Custom DB path (e.g. staging)
python core/migrations/env.py --memory-path /tmp/gaia_memory.db --ledger-path /tmp/gaia_audit.db
```

## Adding a new migration

1. Create a new `.sql` file following the naming convention:
   `V{NNN}__{description_with_underscores}.sql`
   where `NNN` is zero-padded to 3 digits (e.g. `V005__add_topic_full_text.sql`).
2. Place it in the correct subfolder (`memory/` or `ledger/`).
3. Write idempotent DDL — use `IF NOT EXISTS`, `IF NOT EXISTS` guards or `TRY`/`EXCEPT`
   blocks. The runner marks each file applied only after it executes without error.
4. Run `python core/migrations/env.py --dry-run` to confirm it is detected.
5. Commit the file. The migration runs automatically on next server start
   (the server calls `apply_all()` during startup).

## Rollback

SQLite does not support transactional DDL for all operations (e.g. `DROP INDEX`
is not always transactional). For that reason, **rollback scripts are not
provided** — instead, restore from the most recent database backup.

Backups are written automatically by the server to `data/backups/` before each
migration run.

## Migration versioning table

Both databases contain a `schema_versions` table (created by the runner on first
run) that tracks every applied migration:

```sql
SELECT * FROM schema_versions ORDER BY applied_at;
```

| Column | Type | Description |
|---|---|---|
| version | TEXT PK | Migration filename stem (e.g. `V001__create_memory_items`) |
| applied_at | REAL | Unix timestamp of application |
| checksum | TEXT | SHA-256 of the SQL file content at time of application |
