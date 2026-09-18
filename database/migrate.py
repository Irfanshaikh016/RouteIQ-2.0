"""
RouteIQ 2.0 - Database Migration Runner
Applies sequential SQL migrations to PostgreSQL/Supabase and tracks applied versions.
Usage:
    python database/migrate.py [--status] [--verify]
"""
import os
import sys
import argparse
from pathlib import Path
import psycopg2
from dotenv import load_dotenv

# Load environment from .env or backend/.env
root_dir = Path(__file__).resolve().parent.parent
load_dotenv(root_dir / ".env")
load_dotenv(root_dir / "backend" / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")
MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def get_connection():
    if not DATABASE_URL:
        print("[MIGRATE] ERROR: DATABASE_URL is not set in environment or .env file.")
        print("[MIGRATE] Please set DATABASE_URL (e.g. postgresql://user:pass@localhost:5432/routeiq)")
        sys.exit(1)
    return psycopg2.connect(DATABASE_URL)


def ensure_migration_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                id SERIAL PRIMARY KEY,
                version VARCHAR(128) UNIQUE NOT NULL,
                applied_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            );
        """)
    conn.commit()


def get_applied_migrations(conn):
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations ORDER BY id ASC;")
        rows = cur.fetchall()
        return {r[0] for r in rows}


def apply_migrations(dry_run=False):
    conn = get_connection()
    ensure_migration_table(conn)
    applied = get_applied_migrations(conn)

    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not migration_files:
        print(f"[MIGRATE] No migration files found in {MIGRATIONS_DIR}")
        return

    print(f"[MIGRATE] Found {len(migration_files)} migration files. {len(applied)} already applied.")

    pending = [f for f in migration_files if f.name not in applied]
    if not pending:
        print("[MIGRATE] Schema is up to date. No pending migrations.")
        return

    for mf in pending:
        print(f"[MIGRATE] Processing {mf.name}...")
        if dry_run:
            print(f"[MIGRATE] (Dry run) Would execute {mf.name}")
            continue

        sql = mf.read_text(encoding="utf-8")
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
                cur.execute("INSERT INTO schema_migrations (version) VALUES (%s);", (mf.name,))
            conn.commit()
            print(f"[MIGRATE] Successfully applied {mf.name}")
        except Exception as e:
            conn.rollback()
            print(f"[MIGRATE] FAILED to apply {mf.name}: {e}")
            sys.exit(1)

    conn.close()
    print("[MIGRATE] Migration process complete.")


def check_status():
    conn = get_connection()
    ensure_migration_table(conn)
    applied = get_applied_migrations(conn)
    migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

    print("\n--- RouteIQ 2.0 Database Migrations Status ---")
    for mf in migration_files:
        status_str = "APPLIED" if mf.name in applied else "PENDING"
        print(f"[{status_str:7}] {mf.name}")
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RouteIQ 2.0 Migration Runner")
    parser.add_argument("--status", action="store_true", help="Display migration status")
    parser.add_argument("--verify", action="store_true", help="Verify migrations without running")
    args = parser.parse_args()

    if args.status:
        check_status()
    elif args.verify:
        apply_migrations(dry_run=True)
    else:
        apply_migrations()
