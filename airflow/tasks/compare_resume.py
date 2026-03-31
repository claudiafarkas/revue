"""Compare cleaned resume content against job posting requirements.

This module keeps comparison logic independent from Airflow so it is testable
and reusable outside DAG runtime.
"""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+.#/-]{1,}")

# Small stopword set to keep baseline matching focused.
_STOPWORDS = {
	"a",
	"an",
	"and",
	"any",
	"are",
	"as",
	"at",
	"be",
	"by",
	"can",
	"do",
	"does",
	"each",
	"for",
	"from",
	"have",
	"how",
	"if",
	"in",
	"into",
	"is",
	"it",
	"its",
	"more",
	"of",
	"on",
	"or",
	"our",
	"out",
	"per",
	"than",
	"that",
	"the",
	"their",
	"there",
	"these",
	"they",
	"this",
	"through",
	"time",
	"to",
	"using",
	"we",
	"will",
	"with",
	"you",
	"your",
}


def _tokenize(text: str) -> list[str]:
	"""Tokenize text into lowercase keywords, excluding short stopwords."""
	tokens = [match.group(0).lower() for match in _TOKEN_RE.finditer(text)]
	return [token for token in tokens if token not in _STOPWORDS and len(token) > 2]


def summarize_top_keywords(text: str, limit: int = 25) -> list[str]:
	"""Return the most frequent keywords in descending frequency order."""
	counts = Counter(_tokenize(text))
	return [word for word, _ in counts.most_common(limit)]


def compare_resume_to_postings(
	resume_text: str,
	postings: list[str],
	*,
	top_keywords: int = 40,
) -> dict[str, Any]:
	"""Build a baseline resume/posting comparison summary.

	Returns overlap metrics plus keyword-level hits and gaps that downstream
	report generation can render.
	"""
	if not isinstance(resume_text, str):
		raise TypeError("resume_text must be a string")
	if not isinstance(postings, list) or not all(isinstance(item, str) for item in postings):
		raise TypeError("postings must be a list[str]")

	merged_postings = "\n".join(postings)
	resume_keywords = summarize_top_keywords(resume_text, limit=top_keywords)
	posting_keywords = summarize_top_keywords(merged_postings, limit=top_keywords)

	resume_set = set(resume_keywords)
	posting_set = set(posting_keywords)

	matched = sorted(resume_set & posting_set)
	missing = sorted(posting_set - resume_set)

	denominator = max(len(posting_set), 1)
	match_score = len(matched) / denominator

	return {
		"match_score": round(match_score, 3),
		"matched_keywords": matched,
		"missing_keywords": missing,
		"resume_keywords": resume_keywords,
		"posting_keywords": posting_keywords,
	}


def compare_pipeline_inputs(payload: dict[str, Any]) -> dict[str, Any]:
	"""Attach comparison outputs to pipeline payload and return a copy."""
	postings = payload.get("postings", [])
	resume_text = payload.get("resume_text", "")

	comparison = compare_resume_to_postings(resume_text=resume_text, postings=postings)

	updated_payload = dict(payload)
	updated_payload["comparison"] = comparison
	return updated_payload