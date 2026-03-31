"""Load resume PDF bytes from Postgres and extract plain text."""

import io
import os

import psycopg
from pypdf import PdfReader


def _connection_string(mask_password: bool = False) -> str:
    """Build a psycopg connection string from environment variables."""
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5434")
    db_name = os.getenv("DB_NAME", "revue")
    user = os.getenv("DB_USER", "revue")
    password = os.getenv("DB_PASSWORD", "revue_dev")
    if mask_password:
        password = "***"
    return f"host={host} port={port} dbname={db_name} user={user} password={password}"



def load_resume_text(job_id: str) -> str:
    """Fetch latest resume PDF for a job_id and extract text."""
    if not job_id:
        raise ValueError("job_id is required")

    conn_str = _connection_string()
    with psycopg.connect(conn_str) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT file_data
                FROM resumes
                WHERE job_id = %s
                ORDER BY created_at DESC
                LIMIT 1;
                """,
                (job_id,),
            )
            row = cur.fetchone()

    if row is None or row[0] is None:
        raise ValueError(f"No resume found for job_id '{job_id}'.")

    pdf_bytes = row[0]
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages = [page.extract_text() or "" for page in reader.pages]
    resume_text = "\n".join(pages).strip()

    if not resume_text:
        raise ValueError(f"Resume PDF had no extractable text for job_id '{job_id}'.")

    return resume_text