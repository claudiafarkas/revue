"""PostgreSQL persistence helpers for local Revue development."""

from __future__ import annotations

import logging
import os
import re
from io import BytesIO
from pathlib import Path
from typing import Any

import psycopg
from dotenv import load_dotenv
from pypdf import PdfReader

from api.services.migrations import run_migrations

# Load environment variables from .env file in the project root
env_path = Path(__file__).resolve().parents[3] / ".env"
if env_path.exists():
    load_dotenv(env_path)

logger = logging.getLogger(__name__)

_WHITESPACE_RE = re.compile(r"\s+")


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
    logger.info("Running database migrations")
    run_migrations(connection_string())
    logger.info("Database migrations finished")


def _clean_extracted_page_text(text: str) -> str:
    """Normalize extracted PDF text while preserving line structure."""
    if not text:
        return ""
    text = text.replace("\r", "\n")
    text = text.replace("\u00ad", "")
    text = text.replace("|", " ")
    cleaned_lines: list[str] = []
    for line in text.split("\n"):
        normalized = _WHITESPACE_RE.sub(" ", line).strip()
        if normalized:
            cleaned_lines.append(normalized)
    return "\n".join(cleaned_lines).strip()


def _extract_resume_text_from_bytes(file_data: bytes) -> str:
    """Extract plain text from uploaded resume PDF bytes."""
    reader = PdfReader(BytesIO(file_data))
    page_texts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if not text:
            try:
                text = page.extract_text(extraction_mode="layout") or ""
            except TypeError:
                text = page.extract_text() or ""
        cleaned = _clean_extracted_page_text(text)
        if cleaned:
            page_texts.append(cleaned)
    return "\n".join(page_texts).strip()


def save_job_postings(job_id: str, user_uid: str, postings: list[str]) -> None:
    """Persist a batch of postings under a generated job identifier."""
    logger.info("Saving job postings: job_id=%s user_uid=%s posting_count=%d", job_id, user_uid, len(postings))
    with psycopg.connect(connection_string()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO job_batches (job_id, user_uid)
                VALUES (%s, %s)
                ON CONFLICT (job_id)
                DO UPDATE SET user_uid = EXCLUDED.user_uid;
                """,
                (job_id, user_uid),
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
                INSERT INTO reports (job_id, user_uid, status, stage)
                VALUES (%s, %s, 'awaiting_resume', 'postings_stored')
                ON CONFLICT (job_id)
                DO UPDATE SET
                    user_uid = EXCLUDED.user_uid,
                    status = EXCLUDED.status,
                    stage = EXCLUDED.stage,
                    updated_at = NOW();
                """,
                (job_id, user_uid),
            )
    logger.info("Saved job postings: job_id=%s user_uid=%s", job_id, user_uid)


def save_resume(
    job_id: str,
    user_uid: str,
    filename: str,
    content_type: str | None,
    file_data: bytes,
) -> bool:
    """Persist resume file data to PostgreSQL for an existing job_id.

    Returns False when the job_id does not exist or does not belong to the user.
    """
    logger.info(
        "Saving resume to PostgreSQL: job_id=%s user_uid=%s filename=%s byte_count=%d",
        job_id,
        user_uid,
        filename,
        len(file_data),
    )
    with psycopg.connect(connection_string()) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM job_batches WHERE job_id = %s AND user_uid = %s;", (job_id, user_uid))
            if cur.fetchone() is None:
                logger.warning("Cannot save resume for unknown or unauthorized job_id: job_id=%s user_uid=%s", job_id, user_uid)
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
                INSERT INTO reports (job_id, user_uid, status, stage)
                VALUES (%s, %s, 'queued_for_processing', 'resume_stored')
                ON CONFLICT (job_id)
                DO UPDATE SET
                    user_uid = EXCLUDED.user_uid,
                    status = EXCLUDED.status,
                    stage = EXCLUDED.stage,
                    updated_at = NOW();
                """,
                (job_id, user_uid),
            )

    logger.info("Saved resume metadata and queued processing: job_id=%s user_uid=%s", job_id, user_uid)
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


def get_report_snapshot(job_id: str, user_uid: str) -> dict[str, Any] | None:
    """Return report-tracking fields for a job id."""
    logger.info("Loading report snapshot: job_id=%s user_uid=%s", job_id, user_uid)
    with psycopg.connect(connection_string()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT status, stage, generated_at, report_json IS NOT NULL AS has_report_json
                FROM reports
                WHERE job_id = %s AND user_uid = %s;
                """,
                (job_id, user_uid),
            )
            row = cur.fetchone()

    if row is None:
        logger.info("No report snapshot found: job_id=%s", job_id)
        return None

    logger.info("Loaded report snapshot: job_id=%s status=%s stage=%s has_report=%s", job_id, row[0], row[1], bool(row[3]))
    return {
        "status": row[0],
        "stage": row[1],
        "generated_at": row[2],
        "report_available": bool(row[3]),
    }


def get_report_content(job_id: str, user_uid: str) -> dict[str, Any] | None:
    """Return full persisted report payload for a job id."""
    logger.info("Loading full report content: job_id=%s user_uid=%s", job_id, user_uid)
    with psycopg.connect(connection_string()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT status, stage, report_json
                FROM reports
                WHERE job_id = %s AND user_uid = %s;
                """,
                (job_id, user_uid),
            )
            row = cur.fetchone()

            postings: list[str] = []
            resume_text: str | None = None
            if row is not None:
                cur.execute(
                    """
                    SELECT posting_text
                    FROM job_postings
                    WHERE job_id = %s
                    ORDER BY posting_index ASC;
                    """,
                    (job_id,),
                )
                postings = [posting_row[0] for posting_row in cur.fetchall() if isinstance(posting_row[0], str)]

                cur.execute(
                    """
                    SELECT file_data
                    FROM resumes
                    WHERE job_id = %s
                    ORDER BY uploaded_at DESC
                    LIMIT 1;
                    """,
                    (job_id,),
                )
                resume_row = cur.fetchone()
                if resume_row is not None and resume_row[0] is not None:
                    try:
                        resume_text = _extract_resume_text_from_bytes(resume_row[0])
                    except Exception:
                        logger.exception("Failed to extract resume text for report download: job_id=%s", job_id)

    if row is None:
        logger.info("No full report content found: job_id=%s", job_id)
        return None

    logger.info(
        "Loaded full report content: job_id=%s status=%s stage=%s has_report=%s",
        job_id,
        row[0],
        row[1],
        bool(row[2]),
    )
    return {
        "status": row[0],
        "stage": row[1],
        "report_json": row[2],
        "source_documents": {
            "resume_text": resume_text,
            "postings": postings,
        },
    }


def get_resume_file(job_id: str, user_uid: str) -> dict[str, Any] | None:
    """Return uploaded resume file bytes for an authorized user/job pair."""
    logger.info("Loading resume file for download: job_id=%s user_uid=%s", job_id, user_uid)
    with psycopg.connect(connection_string()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT r.filename, r.content_type, r.file_data
                FROM resumes r
                JOIN job_batches jb ON jb.job_id = r.job_id
                WHERE r.job_id = %s AND jb.user_uid = %s
                ORDER BY r.uploaded_at DESC
                LIMIT 1;
                """,
                (job_id, user_uid),
            )
            row = cur.fetchone()

    if row is None:
        logger.info("No resume file found for download: job_id=%s", job_id)
        return None

    file_data = row[2]
    if isinstance(file_data, memoryview):
        file_data = file_data.tobytes()

    if not isinstance(file_data, (bytes, bytearray)):
        logger.warning("Unexpected resume file data type: job_id=%s type=%s", job_id, type(file_data).__name__)
        return None

    return {
        "filename": row[0] if isinstance(row[0], str) and row[0].strip() else "resume.pdf",
        "content_type": row[1] if isinstance(row[1], str) and row[1].strip() else "application/pdf",
        "file_data": bytes(file_data),
    }


def list_workflow_history(user_uid: str, *, limit: int = 50) -> list[dict[str, Any]]:
    """Return report history rows for a user, newest first."""
    logger.info("Loading workflow history: user_uid=%s limit=%d", user_uid, limit)
    with psycopg.connect(connection_string()) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    r.job_id,
                    COALESCE(r.generated_at, r.updated_at, r.created_at) AS workflow_date,
                    rs.filename,
                    r.report_json
                FROM reports r
                LEFT JOIN resumes rs ON rs.job_id = r.job_id
                WHERE r.user_uid = %s
                  AND r.report_json IS NOT NULL
                ORDER BY COALESCE(r.generated_at, r.updated_at, r.created_at) DESC
                LIMIT %s;
                """,
                (user_uid, limit),
            )
            rows = cur.fetchall()

    history_items: list[dict[str, Any]] = []
    for row in rows:
        report_json = row[3] if isinstance(row[3], dict) else {}
        summary = report_json.get("summary") if isinstance(report_json.get("summary"), dict) else {}
        narrative = report_json.get("narrative") if isinstance(report_json.get("narrative"), dict) else {}
        role_positioning = narrative.get("role_positioning") if isinstance(narrative.get("role_positioning"), dict) else {}

        better_fit_roles = role_positioning.get("better_fit_roles") if isinstance(role_positioning.get("better_fit_roles"), list) else []
        better_fit_roles = [role for role in better_fit_roles if isinstance(role, str) and role.strip()]
        job_family_name = better_fit_roles[0] if better_fit_roles else None

        recommendations = report_json.get("recommendations") if isinstance(report_json.get("recommendations"), list) else []
        recommendations = [item for item in recommendations if isinstance(item, str)]

        history_items.append(
            {
                "job_id": row[0],
                "workflow_date": row[1].isoformat() if row[1] else None,
                "resume_name": row[2] if isinstance(row[2], str) else None,
                "job_family_name": job_family_name,
                "fit_overview": {
                    "match_score": summary.get("match_score") if isinstance(summary.get("match_score"), (int, float)) else None,
                    "fit_level": summary.get("fit_label") if isinstance(summary.get("fit_label"), str) else None,
                    "alignment_similarity": summary.get("embedding_similarity") if isinstance(summary.get("embedding_similarity"), (int, float)) else None,
                },
                "report_preview": {
                    "overview": narrative.get("overview") if isinstance(narrative.get("overview"), str) else "",
                    "strengths_summary": narrative.get("strengths_summary") if isinstance(narrative.get("strengths_summary"), str) else "",
                    "gaps_summary": narrative.get("gaps_summary") if isinstance(narrative.get("gaps_summary"), str) else "",
                    "recommendations": recommendations[:4],
                },
            }
        )

    logger.info("Loaded workflow history rows: user_uid=%s count=%d", user_uid, len(history_items))
    return history_items