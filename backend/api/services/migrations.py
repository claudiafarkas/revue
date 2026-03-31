"""Simple SQL migration runner for local PostgreSQL development."""

from __future__ import annotations

from pathlib import Path

import psycopg


MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"


def run_migrations(connection_string: str) -> None:
    """Apply numbered SQL migration files in order exactly once."""
    with psycopg.connect(connection_string) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """
            )
            cur.execute("SELECT version FROM schema_migrations;")
            applied_versions = {row[0] for row in cur.fetchall()}

        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))
        for migration_path in migration_files:
            version = migration_path.name
            if version in applied_versions:
                continue

            sql = migration_path.read_text(encoding="utf-8")
            with conn.cursor() as cur:
                cur.execute(sql)
                cur.execute(
                    "INSERT INTO schema_migrations (version) VALUES (%s);",
                    (version,),
                )
