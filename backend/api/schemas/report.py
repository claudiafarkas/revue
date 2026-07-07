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


class ReportSourceDocuments(BaseModel):
    """Represent source text used to generate the report."""

    resume_text: str | None = None
    postings: list[str] = []


class ReportContentResponse(BaseModel):
    """Represent full report content once available."""

    job_id: str
    status: str
    stage: str
    report_json: dict[str, Any]
    source_documents: ReportSourceDocuments | None = None


class FitOverview(BaseModel):
    """Represent compact fit metrics for workflow history rows."""

    match_score: float | None = None
    fit_level: str | None = None
    alignment_similarity: float | None = None


class ReportPreview(BaseModel):
    """Represent a concise report preview for account history popups."""

    overview: str = ""
    strengths_summary: str = ""
    gaps_summary: str = ""
    recommendations: list[str] = []


class WorkflowHistoryItem(BaseModel):
    """Represent one historical workflow row for an authenticated user."""

    job_id: str
    workflow_date: str | None = None
    resume_name: str | None = None
    job_family_name: str | None = None
    fit_overview: FitOverview
    report_preview: ReportPreview


class WorkflowHistoryResponse(BaseModel):
    """Represent account workflow history table payload."""

    items: list[WorkflowHistoryItem]