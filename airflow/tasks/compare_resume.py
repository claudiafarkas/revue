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
	"able",
	"about",
	"across",
	"aligned",
	"about",
	"an",
	"and",
	"and-or",
	"and",
	"and/or",
	"any",
	"appropriate",
	"are",
	"as",
	"at",
	"background",
	"be",
	"both",
	"by",
	"can",
	"capable",
	"candidate",
	"candidates",
	"collaborate",
	"collaboration",
	"communication",
	"complex",
	"demonstrated",
	"demonstrates",
	"demonstrating",
	"design",
	"develop",
	"developed",
	"developing",
	"do",
	"does",
	"each",
	"ensure",
	"ensuring",
	"etc",
	"experience",
	"familiar",
	"familiarity",
	"for",
	"from",
	"have",
	"how",
	"if",
	"including",
	"in",
	"into",
	"is",
	"it",
	"its",
	"knowledge",
	"maintain",
	"maintaining",
	"multiple",
	"more",
	"of",
	"on",
	"or",
	"other",
	"our",
	"out",
	"per",
	"preferred",
	"problem",
	"problems",
	"professional",
	"relevant",
	"responsible",
	"role",
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
	"understanding",
	"using",
	"various",
	"we",
	"well",
	"will",
	"with",
	"within",
	"you",
	"your",
}


def normalize_keyword(value: str) -> str:
	"""Normalize raw keyword-like values before filtering and scoring."""
	cleaned = value.strip().lower()
	cleaned = cleaned.replace("&", "/")
	cleaned = re.sub(r"\s+", " ", cleaned)
	cleaned = re.sub(r"\b(and|or)\s*/\s*(and|or)\b", "and/or", cleaned)
	cleaned = re.sub(r"\b(and|or)\s+(and|or)\b", "and/or", cleaned)
	return cleaned


def is_meaningful_keyword(value: str) -> bool:
	"""Return True when a keyword should be included in scoring and report output."""
	cleaned = normalize_keyword(value)
	if len(cleaned) <= 2:
		return False
	if cleaned in _STOPWORDS:
		return False
	if cleaned.replace("/", "") in {"andor", "orand"}:
		return False
	return True


def filter_meaningful_keywords(values: list[str]) -> list[str]:
	"""Normalize, dedupe, and keep only meaningful keywords preserving first-seen order."""
	seen: set[str] = set()
	filtered: list[str] = []
	for value in values:
		cleaned = normalize_keyword(value)
		if not is_meaningful_keyword(cleaned):
			continue
		if cleaned in seen:
			continue
		seen.add(cleaned)
		filtered.append(cleaned)
	return filtered


def _tokenize(text: str) -> list[str]:
	"""Tokenize text into lowercase keywords, excluding stopwords and filler compounds."""
	tokens = [match.group(0).lower() for match in _TOKEN_RE.finditer(text)]
	return filter_meaningful_keywords(tokens)


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