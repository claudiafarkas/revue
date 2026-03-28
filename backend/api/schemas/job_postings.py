"""Schemas for job posting submission endpoints."""

from pydantic import BaseModel, Field


class JobPostingsSubmissionRequest(BaseModel):
    """Validate the initial set of job postings submitted by the frontend."""

    postings: list[str] = Field(
        ...,
        min_length=3,
        description="At least three job posting URLs or pasted descriptions.",
    )


class JobPostingsSubmissionResponse(BaseModel):
    """Describe the accepted job posting batch."""

    job_id: str
    posting_count: int
    status: str
    detail: str