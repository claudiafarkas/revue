"""Load job posting text from PostgreSQL for a pipeline run."""

from __future__ import annotations

import os
from typing import Any
import psycopg


def _connection_string(mask_password: bool = False) -> str:
    """Build a PostgreSQL connection string from environment variables."""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5434")
    db_name = os.getenv("DB_NAME", "revue")
    user = os.getenv("DB_USER", "revue")
    password = os.getenv("DB_PASSWORD", "revue_dev")
    if mask_password:
        password = "***"
    return f"host={host} port={port} dbname={db_name} user={user} password={password}"


def load_job_postings_text_payload(job_id: str) -> dict[str, Any]:
    """Return pipeline payload containing job posting text for a job id.

    Raises:
        ValueError: If no postings exist for the provided job_id.
    """
    with psycopg.connect(_connection_string()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT posting_text
                FROM job_postings
                WHERE job_id = %s
                ORDER BY posting_index ASC;
                """,
                (job_id,),
            )
            rows = cur.fetchall()

    postings = [row[0] for row in rows if row and row[0]]
    if not postings:
        raise ValueError(f"No job postings found for job_id '{job_id}'")

    return {
        "job_id": job_id,
        "postings": postings,
    }