"""Helpers to update report processing status/stage in PostgreSQL."""

from __future__ import annotations

import os

import psycopg


def _connection_string() -> str:
    """Build a psycopg connection string from environment variables."""
    required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError(f"Missing required DB environment variables: {', '.join(missing)}")

    host = os.environ["DB_HOST"]
    port = os.environ["DB_PORT"]
    db_name = os.environ["DB_NAME"]
    user = os.environ["DB_USER"]
    password = os.environ["DB_PASSWORD"]
    return f"host={host} port={port} dbname={db_name} user={user} password={password}"


def update_report_stage(job_id: str, stage: str, status: str = "processing") -> None:
    """Write the current pipeline stage and status for a job id."""
    if not isinstance(job_id, str) or not job_id:
        raise TypeError("job_id must be a non-empty string")
    if not isinstance(stage, str) or not stage:
        raise TypeError("stage must be a non-empty string")
    if not isinstance(status, str) or not status:
        raise TypeError("status must be a non-empty string")

    with psycopg.connect(_connection_string()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO reports (job_id, status, stage)
                VALUES (%s, %s, %s)
                ON CONFLICT (job_id)
                DO UPDATE SET
                    status = EXCLUDED.status,
                    stage = EXCLUDED.stage,
                    updated_at = NOW();
                """,
                (job_id, status, stage),
            )
