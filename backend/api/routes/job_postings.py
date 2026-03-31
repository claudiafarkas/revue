"""Routes for storing and validating job postings."""

from uuid import uuid4
from fastapi import APIRouter, HTTPException, status
from api.schemas.job_postings import JobPostingsSubmissionRequest, JobPostingsSubmissionResponse
from api.services.database import save_job_postings

router = APIRouter(prefix="/job-postings", tags=["job-postings"])


@router.post("", response_model=JobPostingsSubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
def create_job_postings(
	payload: JobPostingsSubmissionRequest,
) -> JobPostingsSubmissionResponse:
	"""Accept job postings and persist them with a tracking identifier."""
	job_id = f"revue-{uuid4().hex[:12]}"			# Generate a short unique job ID with a prefix for easier identification in the database

	try:
		save_job_postings(job_id=job_id, postings=payload.postings)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Unable to store job postings in PostgreSQL.",
		) from exc

	return JobPostingsSubmissionResponse(
		job_id=job_id,
		posting_count=len(payload.postings),
		status="awaiting_resume",
		detail="Job postings accepted and stored.",
	)