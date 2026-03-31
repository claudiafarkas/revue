"""Load job posting text from PostgreSQL for a pipeline run."""

from __future__ import annotations

import os
from typing import Any
import logging
import psycopg

logger = logging.getLogger(__name__)


def _connection_string(mask_password: bool = False) -> str:
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


def load_job_postings_text_payload(job_id: str) -> dict[str, Any]:
    """Return pipeline payload containing job posting text for a job id.

    Raises:
        ValueError: If no postings exist for the provided job_id.
    """
    logger.info("Loading job postings for payload: job_id=%s", job_id)
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
        logger.error("No job postings found: job_id=%s", job_id)
        raise ValueError(f"No job postings found for job_id '{job_id}'")

    logger.info("Loaded job postings: job_id=%s posting_count=%d", job_id, len(postings))

    return {
        "job_id": job_id,
        "postings": postings,
    }