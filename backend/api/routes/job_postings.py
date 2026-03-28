"""Routes for storing and validating job postings."""

from uuid import uuid4

from fastapi import APIRouter, status

from api.schemas.job_postings import JobPostingsSubmissionRequest, JobPostingsSubmissionResponse

router = APIRouter(prefix="/job-postings", tags=["job-postings"])


@router.post("", response_model=JobPostingsSubmissionResponse, status_code=status.HTTP_202_ACCEPTED)
def create_job_postings(
	payload: JobPostingsSubmissionRequest,
) -> JobPostingsSubmissionResponse:
	"""Accept job postings and return a placeholder tracking identifier."""
	return JobPostingsSubmissionResponse(
		job_id=f"revue-{uuid4().hex[:12]}",
		posting_count=len(payload.postings),
		status="awaiting_resume",
		detail="Job postings accepted. Persistence will be wired into FastAPI services next.",
	)