"""Routes for report status and retrieval."""

from fastapi import APIRouter, HTTPException, status

from api.schemas.report import ReportStatusResponse
from api.services.database import get_report_snapshot

router = APIRouter(prefix="/report", tags=["report"])


@router.get("/{job_id}", response_model=ReportStatusResponse)
def get_report_status(job_id: str) -> ReportStatusResponse:
	"""Return current status based on the report-tracking table."""
	try:
		snapshot = get_report_snapshot(job_id)
	except Exception as exc:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Unable to read report status from PostgreSQL.",
		) from exc

	if snapshot is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=f"Unknown job_id '{job_id}'.",
		)

	return ReportStatusResponse(
		job_id=job_id,
		status=snapshot["status"],
		stage=snapshot["stage"],
		report_available=snapshot["report_available"],
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