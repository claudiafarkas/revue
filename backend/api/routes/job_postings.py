"""Routes for storing and validating job postings."""

import logging
from uuid import uuid4
from fastapi import APIRouter, HTTPException, status
from api.schemas.job_postings import JobPostingsSubmissionRequest, JobPostingsSubmissionResponse
from api.services.database import save_job_postings

router = APIRouter(prefix="/job-postings", tags=["job-postings"])
logger = logging.getLogger(__name__)


@router.post("", response_model=JobPostingsSubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
def create_job_postings(
	payload: JobPostingsSubmissionRequest,
) -> JobPostingsSubmissionResponse:
	"""Accept job postings and persist them with a tracking identifier."""
	job_id = f"revue-{uuid4().hex[:12]}"			# Generate a short unique job ID with a prefix for easier identification in the database
	logger.info("Received job postings submission: job_id=%s posting_count=%d", job_id, len(payload.postings))

	try:
		save_job_postings(job_id=job_id, postings=payload.postings)
	except Exception as exc:
		logger.exception("Failed to store job postings: job_id=%s", job_id)
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Unable to store job postings in PostgreSQL.",
		) from exc

	logger.info("Stored job postings successfully: job_id=%s", job_id)

	return JobPostingsSubmissionResponse(
		job_id=job_id,
		posting_count=len(payload.postings),
		status="awaiting_resume",
		detail="Job postings accepted and stored.",
	)