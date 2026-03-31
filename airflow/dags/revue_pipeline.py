"""Revue.ai processing pipeline DAG."""
import logging
import os
import psycopg
from datetime import datetime, timedelta
from typing import Any

from airflow import DAG
from airflow.decorators import task

import tasks.clean_text
import tasks.compare_resume
import tasks.extract_job_postings_text
import tasks.extract_resume_features
import tasks.extract_resume_text
import tasks.generate_embeddings
import tasks.generate_report
import tasks.llm_analysis
import tasks.report_status
import tasks.store_output

logger = logging.getLogger(__name__)


def _payload_summary(payload: dict[str, Any]) -> str:
    postings = payload.get("postings")
    resume_text = payload.get("resume_text")
    return (
        f"job_id={payload.get('job_id')} "
        f"postings={len(postings) if isinstance(postings, list) else 'n/a'} "
        f"resume_chars={len(resume_text) if isinstance(resume_text, str) else 'n/a'} "
        f"keys={sorted(payload.keys())}"
    )


# Step 6: Failure handling callback used by default_args.
def on_pipeline_failure(context: dict) -> None:
    """Mark reports row as failed when any DAG task raises an exception."""

    dag_run = context.get("dag_run")
    job_id = dag_run.conf.get("job_id") if dag_run and dag_run.conf else None
    if not job_id:
        logger.warning("Pipeline failure callback invoked without job_id")
        return
    logger.error("Pipeline failure callback invoked: job_id=%s", job_id)

    required = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    if any(not os.getenv(key) for key in required):
        logger.error("Cannot mark pipeline failure due to missing DB environment variables: job_id=%s", job_id)
        return

    host = os.environ["DB_HOST"]
    port = os.environ["DB_PORT"]
    db_name = os.environ["DB_NAME"]
    user = os.environ["DB_USER"]
    password = os.environ["DB_PASSWORD"]
    conn_str = f"host={host} port={port} dbname={db_name} user={user} password={password}"

    try:
        with psycopg.connect(conn_str) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE reports SET status = 'failed', stage = 'pipeline_failed', updated_at = NOW() WHERE job_id = %s;",
                    (job_id,),
                )
        logger.error("Marked pipeline as failed in reports table: job_id=%s", job_id)
    except Exception:
        logger.exception("Failed to mark pipeline failure in reports table: job_id=%s", job_id)


    # Step 4: Runtime config readers from dag_run.conf.
@task
def get_job_id_from_conf(**context: Any) -> str:
    """Read job_id from dag_run.conf and fail fast if it is missing."""
    dag_run = context.get("dag_run")
    conf = dag_run.conf if dag_run else {}
    job_id = conf.get("job_id")
    if not isinstance(job_id, str) or not job_id:
        raise ValueError("job_id must be provided in dag_run.conf")
    logger.info("DAG run started: job_id=%s", job_id)
    return job_id


# Step 2: Task wrappers that call reusable task-module functions.
@task
def build_initial_payload(job_id: str, resume_text: str) -> dict[str, Any]:
    """Load postings by job_id and attach resume text for downstream tasks."""
    logger.info("Starting build_initial_payload: job_id=%s resume_chars=%d", job_id, len(resume_text))
    tasks.report_status.update_report_stage(job_id=job_id, stage="loading_postings")
    payload = tasks.extract_job_postings_text.load_job_postings_text_payload(job_id)
    payload["resume_text"] = resume_text
    logger.info("Completed build_initial_payload: %s", _payload_summary(payload))
    return payload


@task
def clean_step(payload: dict[str, Any]) -> dict[str, Any]:
    logger.info("Starting clean_step: %s", _payload_summary(payload))
    tasks.report_status.update_report_stage(job_id=payload["job_id"], stage="cleaning_text")
    cleaned_payload = tasks.clean_text.clean_pipeline_inputs(payload)
    logger.info("Completed clean_step: %s", _payload_summary(cleaned_payload))
    return cleaned_payload


@task
def resume_features_step(payload: dict[str, Any]) -> dict[str, Any]:
    logger.info("Starting resume_features_step: %s", _payload_summary(payload))
    tasks.report_status.update_report_stage(job_id=payload["job_id"], stage="extracting_resume_features")
    updated_payload = tasks.extract_resume_features.extract_resume_features_from_payload(payload)
    features = updated_payload.get("resume_features", {})
    logger.info(
        "Completed resume_features_step: job_id=%s features_keys=%s keyword_count=%s",
        payload["job_id"],
        sorted(features.keys()) if isinstance(features, dict) else "n/a",
        len(features.get("keywords", [])) if isinstance(features, dict) else "n/a",
    )
    return updated_payload


@task
def extract_resume_text_step(job_id: str) -> str:
    logger.info("Starting extract_resume_text_step: job_id=%s", job_id)
    tasks.report_status.update_report_stage(job_id=job_id, stage="extracting_resume_text")
    resume_text = tasks.extract_resume_text.load_resume_text(job_id)
    logger.info("Completed extract_resume_text_step: job_id=%s resume_chars=%d", job_id, len(resume_text))
    return resume_text


@task
def compare_step(payload: dict[str, Any]) -> dict[str, Any]:
    logger.info("Starting compare_step: %s", _payload_summary(payload))
    tasks.report_status.update_report_stage(job_id=payload["job_id"], stage="comparing_requirements")
    updated_payload = tasks.compare_resume.compare_pipeline_inputs(payload)
    comparison = updated_payload.get("comparison", {})
    logger.info(
        "Completed compare_step: job_id=%s match_score=%s matched=%s missing=%s",
        payload["job_id"],
        comparison.get("match_score") if isinstance(comparison, dict) else "n/a",
        len(comparison.get("matched_keywords", [])) if isinstance(comparison, dict) else "n/a",
        len(comparison.get("missing_keywords", [])) if isinstance(comparison, dict) else "n/a",
    )
    return updated_payload


@task
def llm_analysis_step(payload: dict[str, Any]) -> dict[str, Any]:
    logger.info("Starting llm_analysis_step: %s", _payload_summary(payload))
    tasks.report_status.update_report_stage(job_id=payload["job_id"], stage="analyzing_with_llm")
    updated_payload = tasks.llm_analysis.analyze_with_llm(payload)
    llm_available = bool(updated_payload.get("llm_analysis"))
    logger.info(
        "Completed llm_analysis_step: job_id=%s llm_available=%s",
        payload["job_id"],
        llm_available,
    )
    return updated_payload


@task
def embeddings_step(payload: dict[str, Any]) -> dict[str, Any]:
    logger.info("Starting embeddings_step: %s", _payload_summary(payload))
    tasks.report_status.update_report_stage(job_id=payload["job_id"], stage="generating_embeddings")
    updated_payload = tasks.generate_embeddings.generate_embeddings_from_payload(payload)
    embedding_features = updated_payload.get("embedding_features", {})
    logger.info(
        "Completed embeddings_step: job_id=%s average_similarity=%s posting_vectors=%s",
        payload["job_id"],
        embedding_features.get("average_similarity") if isinstance(embedding_features, dict) else "n/a",
        len(embedding_features.get("posting_vectors", [])) if isinstance(embedding_features, dict) else "n/a",
    )
    return updated_payload


@task
def report_step(payload: dict[str, Any]) -> dict[str, Any]:
    logger.info("Starting report_step: %s", _payload_summary(payload))
    tasks.report_status.update_report_stage(job_id=payload["job_id"], stage="generating_report")
    updated_payload = tasks.generate_report.generate_report_from_payload(payload)
    report_json = updated_payload.get("report_json", {})
    logger.info(
        "Completed report_step: job_id=%s report_keys=%s",
        payload["job_id"],
        sorted(report_json.keys()) if isinstance(report_json, dict) else "n/a",
    )
    return updated_payload


@task
def store_step(payload: dict[str, Any]) -> dict[str, Any]:
    logger.info("Starting store_step: %s", _payload_summary(payload))
    updated_payload = tasks.store_output.store_output_from_payload(payload)
    logger.info(
        "Completed store_step: job_id=%s status=%s stage=%s",
        payload.get("job_id"),
        updated_payload.get("status"),
        updated_payload.get("stage"),
    )
    return updated_payload


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
    payload = llm_analysis_step(payload)
    payload = embeddings_step(payload)
    payload = report_step(payload)

    # Step 7: Final persistence and completion status update.
    store_step(payload)

