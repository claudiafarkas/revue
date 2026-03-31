"""Routes for resume upload and ingestion."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from api.schemas.resume import ResumeUploadResponse
from api.services.database import save_resume
from api.services.airflow_trigger import trigger_airflow_dag

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("", response_model=ResumeUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_resume(
    job_id: str = Form(...),
    file: UploadFile = File(...),
) -> ResumeUploadResponse:
    """Accept a PDF resume and persist it for the provided job id."""
    filename = file.filename or "resume.pdf"        # file validation

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume must be uploaded as a PDF.")

    file_data = await file.read()

    try:
        saved = save_resume(
            job_id=job_id,
            filename=filename,
            content_type=file.content_type,
            file_data=file_data,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to store resume in PostgreSQL.",
        ) from exc

    if not saved:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown job_id '{job_id}'. Submit job postings first.",        # checks if the jobid is the same
        )

    try:
        trigger_airflow_dag(job_id=job_id)  # call the Airflow DAG trigger service here to start the processing pipeline for the uploaded resume, passing the job_id as a parameter to trigger the correct DAG run for this job_id
    except Exception as exc:
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

