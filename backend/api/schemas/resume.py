"""Schemas for resume upload acknowledgements."""

from pydantic import BaseModel


class ResumeUploadResponse(BaseModel):
    """Return the backend acknowledgement for an uploaded resume."""

    job_id: str
    filename: str
    status: str
    detail: str