"""Load resume PDF bytes from Postgres and extract plain text."""

import io
import logging
import os

import psycopg
from pypdf import PdfReader

logger = logging.getLogger(__name__)


def _connection_string(mask_password: bool = False) -> str:
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
    if mask_password:
        password = "***"
    return f"host={host} port={port} dbname={db_name} user={user} password={password}"



def load_resume_text(job_id: str) -> str:
    """Fetch latest resume PDF for a job_id and extract text."""
    if not job_id:
        raise ValueError("job_id is required")

    logger.info("Loading resume PDF from database: job_id=%s", job_id)
    conn_str = _connection_string()
    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cur:
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
            row = cur.fetchone()

    if row is None or row[0] is None:
        logger.error("No resume file_data found: job_id=%s", job_id)
        raise ValueError(f"No resume found for job_id '{job_id}'.")

    pdf_bytes = row[0]
    logger.info("Resume bytes loaded: job_id=%s byte_count=%d", job_id, len(pdf_bytes))
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    resume_text = "\n".join(pages).strip()

    if not resume_text:
        logger.error("Resume text extraction produced empty text: job_id=%s page_count=%d", job_id, len(pages))
        raise ValueError(f"Resume PDF had no extractable text for job_id '{job_id}'.")

    logger.info("Resume text extracted: job_id=%s page_count=%d char_count=%d", job_id, len(pages), len(resume_text))
    return resume_text