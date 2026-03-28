"""Routes for report status and retrieval."""

from fastapi import APIRouter, HTTPException, status

from api.schemas.report import ReportStatusResponse

router = APIRouter(prefix="/report", tags=["report"])


@router.get("/{job_id}", response_model=ReportStatusResponse)
def get_report_status(job_id: str) -> ReportStatusResponse:
	"""Return a placeholder status payload for the requested report."""
	return ReportStatusResponse(
		job_id=job_id,
		status="pending_pipeline",
		stage="backend_shell_ready",
		report_available=False,
		poll_after_seconds=5,
	)


@router.get("/{job_id}/download")
def download_report(job_id: str) -> None:
	"""Reserve the final report download route without implementing storage yet."""
	raise HTTPException(
		status_code=status.HTTP_501_NOT_IMPLEMENTED,
		detail=(
			f"Report download for '{job_id}' is not available yet. "
			"PDF generation and storage will be implemented later."
		),
	)