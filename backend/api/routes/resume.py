"""Routes for resume upload and ingestion."""

import logging
import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from api.schemas.resume import ResumeUploadResponse
from api.services.auth import AuthenticatedUser, get_current_user
from api.services.database import save_resume
from api.services.airflow_trigger import trigger_airflow_dag

router = APIRouter(prefix="/resume", tags=["resume"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ResumeUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_resume(
    job_id: str = Form(...),
    filename: str = Form(...),
    content_type: str | None = Form(None),
    file: UploadFile = File(...),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ResumeUploadResponse:
    """Accept resume file and persist to PostgreSQL for the provided job id."""
    logger.info(
        "Resume upload requested: job_id=%s filename=%s uid=%s",
        job_id,
        filename,
        current_user.uid,
    )

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume must be uploaded as a PDF.")

    try:
        file_data = await file.read()
        logger.info("Read resume bytes: job_id=%s byte_count=%d", job_id, len(file_data))
    except Exception as exc:
        logger.exception("Failed to read uploaded file: job_id=%s", job_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to read uploaded file.",
        ) from exc

    try:
        saved = save_resume(
            job_id=job_id,
            user_uid=current_user.uid,
            filename=filename,
            content_type=content_type,
            file_data=file_data,
        )
    except Exception as exc:
        logger.exception("Failed to save resume in database: job_id=%s filename=%s", job_id, filename)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to store resume in PostgreSQL.",
        ) from exc

    if not saved:
        logger.warning("Resume upload rejected due to unknown or unauthorized job_id: job_id=%s uid=%s", job_id, current_user.uid)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown job_id '{job_id}' for current user. Submit job postings first.",
        )

    try:
        dag_run_id = trigger_airflow_dag(job_id=job_id)  # call the Airflow DAG trigger service here to start the processing pipeline for the uploaded resume, passing the job_id as a parameter to trigger the correct DAG run for this job_id
        logger.info("Triggered Airflow DAG successfully: job_id=%s dag_run_id=%s", job_id, dag_run_id)
    except Exception as exc:
        logger.exception("Failed to trigger Airflow DAG: job_id=%s", job_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Resume stored, but failed to trigger processing pipeline.",
        ) from exc

    return ResumeUploadResponse(
        job_id=job_id,
        filename=filename,
        status="queued_for_processing",
        detail="Resume accepted and stored.",
    )

