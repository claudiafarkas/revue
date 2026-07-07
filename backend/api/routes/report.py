"""Routes for report status and retrieval."""

import logging
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Response, status

from api.schemas.report import ReportContentResponse, ReportStatusResponse, WorkflowHistoryResponse
from api.services.auth import AuthenticatedUser, get_current_user
from api.services.database import get_report_content, get_report_snapshot, get_resume_file, list_workflow_history

router = APIRouter(prefix="/report", tags=["report"])
logger = logging.getLogger(__name__)


@router.get("/history", response_model=WorkflowHistoryResponse)
def get_workflow_history_route(
	current_user: AuthenticatedUser = Depends(get_current_user),
) -> WorkflowHistoryResponse:
	"""Return historical workflow rows for the authenticated user account page."""
	logger.info("Workflow history requested: uid=%s", current_user.uid)
	try:
		items = list_workflow_history(current_user.uid)
	except Exception as exc:
		logger.exception("Failed to load workflow history: uid=%s", current_user.uid)
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Unable to read workflow history from PostgreSQL.",
		) from exc

	return WorkflowHistoryResponse(items=items)


@router.get("/{job_id}", response_model=ReportStatusResponse)
def get_report_status(
	job_id: str,
	current_user: AuthenticatedUser = Depends(get_current_user),
) -> ReportStatusResponse:
	"""Return current status based on the report-tracking table."""
	logger.info("Report status requested: job_id=%s uid=%s", job_id, current_user.uid)
	try:
		snapshot = get_report_snapshot(job_id, current_user.uid)
	except Exception as exc:
		logger.exception("Failed to read report status: job_id=%s", job_id)
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Unable to read report status from PostgreSQL.",
		) from exc

	if snapshot is None:
		logger.warning("Report status not found: job_id=%s", job_id)
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=f"Unknown job_id '{job_id}'.",
		)

	logger.info(
		"Report status response: job_id=%s status=%s stage=%s report_available=%s",
		job_id,
		snapshot["status"],
		snapshot["stage"],
		snapshot["report_available"],
	)

	return ReportStatusResponse(
		job_id=job_id,
		status=snapshot["status"],
		stage=snapshot["stage"],
		report_available=snapshot["report_available"],
		poll_after_seconds=5,
	)


@router.get("/{job_id}/content", response_model=ReportContentResponse)
def get_report_content_route(
	job_id: str,
	current_user: AuthenticatedUser = Depends(get_current_user),
) -> ReportContentResponse:
	"""Return persisted report_json content for rendering the report page."""
	logger.info("Report content requested: job_id=%s uid=%s", job_id, current_user.uid)
	try:
		snapshot = get_report_content(job_id, current_user.uid)
	except Exception as exc:
		logger.exception("Failed to read report content: job_id=%s", job_id)
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Unable to read report content from PostgreSQL.",
		) from exc

	if snapshot is None:
		logger.warning("Report content not found: job_id=%s", job_id)
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=f"Unknown job_id '{job_id}'.",
		)

	report_json = snapshot.get("report_json")
	if not isinstance(report_json, dict) or not report_json:
		logger.warning("Report content empty or not ready: job_id=%s status=%s stage=%s", job_id, snapshot.get("status"), snapshot.get("stage"))
		raise HTTPException(
			status_code=status.HTTP_409_CONFLICT,
			detail="Report content is not available yet for this job.",
		)

	logger.info("Report content response: job_id=%s keys=%s", job_id, sorted(report_json.keys()))
	source_documents = snapshot.get("source_documents")
	if source_documents is not None and not isinstance(source_documents, dict):
		source_documents = None
	return ReportContentResponse(
		job_id=job_id,
		status=snapshot["status"],
		stage=snapshot["stage"],
		report_json=report_json,
		source_documents=source_documents,
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


@router.get("/{job_id}/resume-file")
def get_report_resume_file(
	job_id: str,
	current_user: AuthenticatedUser = Depends(get_current_user),
) -> Response:
	"""Return the uploaded resume PDF file for embedding in report exports."""
	logger.info("Resume file requested for report: job_id=%s uid=%s", job_id, current_user.uid)
	try:
		resume_file = get_resume_file(job_id, current_user.uid)
	except Exception as exc:
		logger.exception("Failed to load resume file for report: job_id=%s", job_id)
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail="Unable to load resume file from PostgreSQL.",
		) from exc

	if resume_file is None:
		raise HTTPException(
			status_code=status.HTTP_404_NOT_FOUND,
			detail=f"No uploaded resume found for job_id '{job_id}'.",
		)

	filename = resume_file["filename"]
	encoded_filename = quote(filename)
	return Response(
		content=resume_file["file_data"],
		media_type=resume_file["content_type"],
		headers={
			"Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}",
		},
	)