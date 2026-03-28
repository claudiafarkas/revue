"""Schemas for report polling and status responses."""

from pydantic import BaseModel


class ReportStatusResponse(BaseModel):
    """Represent the current status of report generation."""

    job_id: str
    status: str
    stage: str
    report_available: bool
    poll_after_seconds: int