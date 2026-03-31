"""Utilities for normalizing and cleaning extracted text inputs.

This module is intentionally plain Python so it can be reused by Airflow tasks,
unit tests, and local scripts without requiring an Airflow runtime.
"""

from __future__ import annotations

import html
import re
import unicodedata
from typing import Any

_WHITESPACE_RE = re.compile(r"\s+")
_BULLET_PREFIX_RE = re.compile(r"^[\s\-*•·]+")
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]")


def clean_text_block(raw_text: str, *, keep_line_breaks: bool = True) -> str:
	"""Return a normalized, readable version of a text block.

	Steps:
	1. Unicode normalize to reduce odd glyph variants.
	2. Decode HTML entities when present.
	3. Strip control characters that commonly appear in scraped text.
	4. Normalize whitespace while optionally preserving line structure.
	5. Trim simple leading bullet prefixes on each line.
	"""
	if not raw_text:
		return ""

	text = unicodedata.normalize("NFKC", raw_text)
	text = html.unescape(text)
	text = _CONTROL_CHAR_RE.sub("", text)

	if keep_line_breaks:
		cleaned_lines: list[str] = []
		for line in text.splitlines():
			line = _WHITESPACE_RE.sub(" ", line).strip()
			line = _BULLET_PREFIX_RE.sub("", line).strip()
			if line:
				cleaned_lines.append(line)
		return "\n".join(cleaned_lines)

	text = _WHITESPACE_RE.sub(" ", text)
	text = _BULLET_PREFIX_RE.sub("", text).strip()
	return text


def clean_job_postings(postings: list[str]) -> list[str]:
	"""Normalize all job posting strings and drop empty results."""
	cleaned = [clean_text_block(posting, keep_line_breaks=True) for posting in postings]
	return [posting for posting in cleaned if posting]


def clean_pipeline_inputs(payload: dict[str, Any]) -> dict[str, Any]:
	"""Clean shared pipeline input payload and return a copied structure.

	Expected payload shape (minimum):
	- job_id: str
	- postings: list[str]
	- resume_text: str
	"""
	postings = payload.get("postings", [])
	if not isinstance(postings, list):
		raise TypeError("'postings' must be a list of strings")

	resume_text = payload.get("resume_text", "")
	if not isinstance(resume_text, str):
		raise TypeError("'resume_text' must be a string")

	cleaned_payload = dict(payload)
	cleaned_payload["postings"] = clean_job_postings(postings)
	cleaned_payload["resume_text"] = clean_text_block(resume_text, keep_line_breaks=True)
	return cleaned_payload