"""PostgreSQL persistence helpers for local Revue development."""

from __future__ import annotations

import os
from typing import Any

import psycopg

from api.services.migrations import run_migrations


def connection_string(mask_password: bool = False) -> str:
    """Build a PostgreSQL connection string from environment variables."""
    required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError(f"Missing required DB environment variables: {', '.join(missing)}")

    host = os.environ["DB_HOST"]
    port = os.environ["DB_PORT"]
    db_name = os.environ["DB_NAME"]
    user = os.environ["DB_USER"]
    password = os.environ["DB_PASSWORD"]
    if mask_password:
        password = "***"
    return f"host={host} port={port} dbname={db_name} user={user} password={password}"


def initialize_database() -> None:
    """Apply SQL migrations to ensure required tables exist."""
    run_migrations(connection_string())


def save_job_postings(job_id: str, postings: list[str]) -> None:
    """Persist a batch of postings under a generated job identifier."""
    with psycopg.connect(connection_string()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO job_batches (job_id)
                VALUES (%s)
                ON CONFLICT (job_id) DO NOTHING;
                """,
                (job_id,),
            )
            rows = [(job_id, idx, posting) for idx, posting in enumerate(postings)]
            cur.executemany(
                """
                INSERT INTO job_postings (job_id, posting_index, posting_text)
                VALUES (%s, %s, %s)
                ON CONFLICT (job_id, posting_index)
                DO UPDATE SET posting_text = EXCLUDED.posting_text;
                """,
                rows,
            )
            cur.execute(
                """
                INSERT INTO reports (job_id, status, stage)
                VALUES (%s, 'awaiting_resume', 'postings_stored')
                ON CONFLICT (job_id)
                DO UPDATE SET
                    status = EXCLUDED.status,
                    stage = EXCLUDED.stage,
                    updated_at = NOW();
                """,
                (job_id,),
            )


def save_resume(job_id: str, filename: str, content_type: str | None, file_data: bytes) -> bool:
    """Persist a resume file for an existing job_id.

    Returns False when the job_id does not exist yet.
    """
    with psycopg.connect(connection_string()) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM job_batches WHERE job_id = %s;", (job_id,))
            if cur.fetchone() is None:
                return False

            cur.execute(
                """
                INSERT INTO resumes (job_id, filename, content_type, file_data)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (job_id)
                DO UPDATE SET
                    filename = EXCLUDED.filename,
                    content_type = EXCLUDED.content_type,
                    file_data = EXCLUDED.file_data,
                    uploaded_at = NOW();
                """,
                (job_id, filename, content_type, file_data),
            )
            cur.execute(
                """
                INSERT INTO reports (job_id, status, stage)
                VALUES (%s, 'queued_for_processing', 'resume_stored')
                ON CONFLICT (job_id)
                DO UPDATE SET
                    status = EXCLUDED.status,
                    stage = EXCLUDED.stage,
                    updated_at = NOW();
                """,
                (job_id,),
            )

    return True


def get_job_snapshot(job_id: str) -> dict[str, Any] | None:
    """Return a lightweight persistence snapshot for report status."""
    with psycopg.connect(connection_string()) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT created_at FROM job_batches WHERE job_id = %s;", (job_id,))
            job_row = cur.fetchone()
            if job_row is None:
                return None

            cur.execute("SELECT COUNT(*) FROM job_postings WHERE job_id = %s;", (job_id,))
            posting_count = int(cur.fetchone()[0])

            cur.execute("SELECT filename FROM resumes WHERE job_id = %s;", (job_id,))
            resume_row = cur.fetchone()

    return {
        "job_id": job_id,
        "posting_count": posting_count,
        "resume_filename": resume_row[0] if resume_row else None,
    }


def get_report_snapshot(job_id: str) -> dict[str, Any] | None:
    """Return report-tracking fields for a job id."""
    with psycopg.connect(connection_string()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT status, stage, generated_at, report_json IS NOT NULL AS has_report_json
                FROM reports
                WHERE job_id = %s;
                """,
                (job_id,),
            )
            row = cur.fetchone()

    if row is None:
        return None

    return {
        "status": row[0],
        "stage": row[1],
        "generated_at": row[2],
        "report_available": bool(row[3]),
    }