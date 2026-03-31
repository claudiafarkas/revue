"""Schemas for report polling and status responses."""

from typing import Any

from pydantic import BaseModel


class ReportStatusResponse(BaseModel):
    """Represent the current status of report generation."""

    job_id: str
    status: str
    stage: str
    report_available: bool
    poll_after_seconds: int


class ReportContentResponse(BaseModel):
    """Represent full report content once available."""

    job_id: str
    status: str
    stage: str
    report_json: dict[str, Any]