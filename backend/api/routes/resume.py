"""Routes for resume upload and ingestion."""

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from api.schemas.resume import ResumeUploadResponse

router = APIRouter(prefix="/resume", tags=["resume"])


@router.post("", response_model=ResumeUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_resume(
    job_id: str = Form(...),
    file: UploadFile = File(...),
) -> ResumeUploadResponse:
    """Accept a PDF resume and acknowledge the future processing step."""
    filename = file.filename or "resume.pdf"

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resume must be uploaded as a PDF.")

    return ResumeUploadResponse(
        job_id=job_id,
        filename=filename,
        status="queued_for_processing",
        detail="Resume accepted. Airflow triggering will be added later.",
    )