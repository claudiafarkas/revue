"""Revue.ai processing pipeline DAG."""
import os
import psycopg
from datetime import datetime, timedelta
from typing import Any

from airflow import DAG
from airflow import task

import tasks.clean_text
import tasks.compare_resume
import tasks.extract_job_postings_text
import tasks.extract_resume_features
import tasks.extract_resume_text
import tasks.generate_embeddings
import tasks.generate_report
import tasks.store_output


# Step 6: Failure handling callback used by default_args.
def on_pipeline_failure(context: dict) -> None:
    """Mark reports row as failed when any DAG task raises an exception."""

    dag_run = context.get("dag_run")
    job_id = dag_run.conf.get("job_id") if dag_run and dag_run.conf else None
    if not job_id:
        return

    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5434")
    db_name = os.getenv("DB_NAME", "revue")
    user = os.getenv("DB_USER", "revue")
    password = os.getenv("DB_PASSWORD", "revue_dev")
    conn_str = f"host={host} port={port} dbname={db_name} user={user} password={password}"

    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE reports SET status = 'failed', updated_at = NOW() WHERE job_id = %s;",
                    (job_id,),
                )
    except Exception:
        pass


    # Step 4: Runtime config readers from dag_run.conf.
@task
def get_job_id_from_conf(**context: Any) -> str:
    """Read job_id from dag_run.conf and fail fast if it is missing."""
    dag_run = context.get("dag_run")
    conf = dag_run.conf if dag_run else {}
    job_id = conf.get("job_id")
    if not isinstance(job_id, str) or not job_id:
        raise ValueError("job_id must be provided in dag_run.conf")
    return job_id


# Step 2: Task wrappers that call reusable task-module functions.
@task
def build_initial_payload(job_id: str, resume_text: str) -> dict[str, Any]:
    """Load postings by job_id and attach resume text for downstream tasks."""
    payload = tasks.extract_job_postings_text.load_job_postings_text_payload(job_id)
    payload["resume_text"] = resume_text
    return payload


@task
def clean_step(payload: dict[str, Any]) -> dict[str, Any]:
    return tasks.clean_text.clean_pipeline_inputs(payload)


@task
def resume_features_step(payload: dict[str, Any]) -> dict[str, Any]:
    return tasks.extract_resume_features.extract_resume_features_from_payload(payload)


@task
def extract_resume_text_step(job_id: str) -> str:
    return tasks.extract_resume_text.load_resume_text(job_id)


@task
def compare_step(payload: dict[str, Any]) -> dict[str, Any]:
    return tasks.compare_resume.compare_pipeline_inputs(payload)


@task
def embeddings_step(payload: dict[str, Any]) -> dict[str, Any]:
    return tasks.generate_embeddings.generate_embeddings_from_payload(payload)


@task
def report_step(payload: dict[str, Any]) -> dict[str, Any]:
    return tasks.generate_report.generate_report_from_payload(payload)


@task
def store_step(payload: dict[str, Any]) -> dict[str, Any]:
    return tasks.store_output.store_output_from_payload(payload)


# Step 1: DAG metadata and execution context.
with DAG(
    dag_id="revue_processing_pipeline",
    schedule=None,
    start_date=datetime(2024, 1, 1),
    default_args={
        "retries": 3,
        "retry_delay": timedelta(minutes=5),
        "on_failure_callback": on_pipeline_failure,
    },
    catchup=False,
) as dag:
    # Step 5: TaskFlow chaining with XCom payload passing.
    job_id = get_job_id_from_conf()
    resume_text = extract_resume_text_step(job_id)

    payload = build_initial_payload(job_id, resume_text)
    payload = clean_step(payload)
    payload = resume_features_step(payload)
    payload = compare_step(payload)
    payload = embeddings_step(payload)
    payload = report_step(payload)

    # Step 7: Final persistence and completion status update.
    store_step(payload)

