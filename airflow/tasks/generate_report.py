"""Assemble a structured report payload from pipeline outputs."""

from __future__ import annotations

import logging
import re
from typing import Any

try:
	from tasks.compare_resume import filter_meaningful_keywords, normalize_keyword
except ModuleNotFoundError:  # pragma: no cover - supports local direct imports
	from .compare_resume import filter_meaningful_keywords, normalize_keyword

logger = logging.getLogger(__name__)

_GENERIC_POSTING_TERMS = {
	"about",
	"across",
	"advantage",
	"analytics",
	"and/or",
	"apply",
	"are",
	"based",
	"across",
	"analytics",
	"apply",
	"better",
	"build",
	"business",
	"can",
	"complex",
	"culture",
	"data",
	"datasets",
	"driven",
	"engineer",
	"engineering",
	"experience",
	"full",
	"how",
	"insights",
	"into",
	"join",
	"jobs",
	"like",
	"locations",
	"need",
	"needs",
	"not",
	"our",
	"posted",
	"problem",
	"problems",
	"product",
	"ready",
	"role",
	"skills",
	"solution",
	"solutions",
	"strategy",
	"stakeholder",
	"software",
	"stakeholders",
	"systems",
	"team",
	"teams",
	"through",
	"time",
	"understand",
	"using",
	"what",
	"work",
	"world",
}

_TOOL_KEYWORDS = {
	"airflow",
	"api",
	"apis",
	"dagster",
	"aws",
	"azure",
	"bigquery",
	"dbt",
	"ci/cd",
	"docker",
	"etl",
	"fastapi",
	"gcp",
	"github",
	"gitlab",
	"java",
	"jira",
	"kafka",
	"kubernetes",
	"looker",
	"mysql",
	"nextjs",
	"node",
	"redshift",
	"postgres",
	"postgresql",
	"python",
	"react",
	"redis",
	"snowflake",
	"spark",
	"sql",
	"tableau",
	"terraform",
	"typescript",
	"snowflake",
	"warehouse",
}

_TECHNICAL_HINTS = {
	"a/b",
	"access",
	"architecture",
	"automation",
	"backend",
	"cloud",
	"code",
	"dashboard",
	"database",
	"devops",
	"etl",
	"integration",
	"kpi",
	"machine learning",
	"ml",
	"pipeline",
	"pipelines",
	"platform",
	"python",
	"sql",
	"terraform",
	"workflow",
	"workflows",
}

_TOOL_ALIASES: dict[str, tuple[str, ...]] = {
	"airflow": ("airflow", "apache airflow"),
	"dagster": ("dagster",),
	"dbt": ("dbt",),
	"docker": ("docker", "containerized applications", "containerized"),
	"python": ("python",),
	"sql": ("sql", "spark sql", "query authoring"),
	"snowflake": ("snowflake",),
	"redshift": ("redshift",),
	"bigquery": ("bigquery",),
	"aws": ("aws",),
	"azure": ("azure",),
	"gcp": ("gcp", "google cloud"),
	"api": ("api", "apis", "restful apis", "rest api", "restful api"),
	"etl": ("etl", "elt"),
	"postgres": ("postgres", "postgresql"),
	"mysql": ("mysql",),
	"spark": ("spark",),
	"kafka": ("kafka",),
	"terraform": ("terraform",),
	"kubernetes": ("kubernetes", "k8s"),
}

_LOW_SIGNAL_GAP_TERMS = {
	"actionable",
	"agile",
	"analysts",
	"built",
	"centralized",
	"citco",
	"collaborating",
	"contributing",
	"controls",
	"enterprise",
	"financial",
	"future",
	"initiatives",
	"junior",
	"maintain",
	"multiple",
	"power",
	"process",
	"processes",
	"strong",
}


def _normalize_keyword_candidates(keywords: list[str]) -> list[str]:
	"""Normalize and keep only meaningful keywords in original order."""
	return filter_meaningful_keywords(keywords)


def _extract_tools_from_text(text: str) -> list[str]:
	"""Extract canonical tool keywords directly from free-form text."""
	if not text:
		return []
	text = text.lower()
	selected: list[str] = []
	for canonical, aliases in _TOOL_ALIASES.items():
		for alias in aliases:
			pattern = rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])"
			if re.search(pattern, text):
				selected.append(canonical)
				break

	# Keep deterministic order with allowlist precedence.
	ordered: list[str] = []
	seen: set[str] = set()
	for keyword in selected:
		if keyword in seen:
			continue
		seen.add(keyword)
		ordered.append(keyword)
	return ordered


def _extract_tools_from_postings(postings: list[str]) -> list[str]:
	"""Extract canonical tool keywords directly from raw posting text."""
	if not postings:
		return []
	return _extract_tools_from_text("\n".join(postings))


def _select_tools_from_posting(posting_keywords: list[str]) -> list[str]:
	"""Extract a tools-first view from posting keywords, keeping only stack terms."""
	candidates = _normalize_keyword_candidates(posting_keywords)
	selected: list[str] = []
	seen: set[str] = set()
	for keyword in candidates:
		cleaned = normalize_keyword(keyword)
		if cleaned not in _TOOL_KEYWORDS and cleaned not in _TECHNICAL_HINTS:
			continue
		if cleaned in seen:
			continue
		seen.add(cleaned)
		selected.append(cleaned)
	return selected


def _score_keyword(keyword: str) -> tuple[int, int, str]:
	"""Rank keywords by technical specificity, tool status, and length."""
	cleaned = normalize_keyword(keyword)
	is_tool = cleaned in _TOOL_KEYWORDS
	is_hint = cleaned in _TECHNICAL_HINTS or any(char in cleaned for char in ("/", "+", ".", "#", "-"))
	is_generic = cleaned in _GENERIC_POSTING_TERMS
	priority = 0 if is_tool else 1 if is_hint else 3 if is_generic else 2
	return (priority, -len(cleaned), cleaned)


def _filter_report_keywords(keywords: list[str]) -> list[str]:
	"""Remove generic language so report sections use only meaningful keywords."""
	filtered = filter_meaningful_keywords(keywords)
	return [keyword for keyword in filtered if normalize_keyword(keyword) not in _GENERIC_POSTING_TERMS]


def _select_common_tools(posting_keywords: list[str], matched_keywords: list[str]) -> list[str]:
	"""Favor technical or tool-like terms over generic recruiting language."""
	posting_tools = _select_tools_from_posting(posting_keywords)
	matched_tools = [keyword for keyword in _filter_report_keywords(matched_keywords) if normalize_keyword(keyword) in _TOOL_KEYWORDS or normalize_keyword(keyword) in _TECHNICAL_HINTS]
	ordered: list[str] = []
	seen: set[str] = set()
	for keyword in posting_tools + matched_tools:
		cleaned = normalize_keyword(keyword)
		if cleaned in seen:
			continue
		seen.add(cleaned)
		ordered.append(cleaned)

	if ordered:
		return ordered[:12]

	# Last-resort fallback only if we failed to detect any tools at all.
	candidates = _filter_report_keywords(posting_keywords + [keyword for keyword in matched_keywords if keyword not in posting_keywords])
	ordered = sorted(candidates, key=_score_keyword)
	return ordered[:12]


def _select_common_achievements(missing_keywords: list[str]) -> list[str]:
	"""Return filtered achievement and emphasis gaps without filler words."""
	return [
		keyword
		for keyword in _filter_report_keywords(missing_keywords)
		if keyword not in _TOOL_KEYWORDS and keyword not in _LOW_SIGNAL_GAP_TERMS
	][:12]


def _filter_gap_keywords(missing_keywords: list[str]) -> list[str]:
	"""Keep under-emphasized terms focused on actionable technical gaps."""
	filtered = _filter_report_keywords(missing_keywords)
	return [keyword for keyword in filtered if keyword not in _LOW_SIGNAL_GAP_TERMS]


def _recompute_match_score(matched_keywords: list[str], missing_keywords: list[str]) -> float:
	"""Recalculate match score from final post-filter keyword sets."""
	matched_count = len(set(matched_keywords))
	missing_count = len(set(missing_keywords))
	denominator = max(matched_count + missing_count, 1)
	return round(matched_count / denominator, 3)


def _compute_tool_overlap_score(tool_keywords: list[str], resume_tools: list[str]) -> float:
	"""Compute tool overlap as a bounded ratio for summary calibration."""
	tool_set = set(tool_keywords)
	if not tool_set:
		return 0.0
	resume_set = set(resume_tools)
	return round(len(tool_set & resume_set) / len(tool_set), 3)


def _looks_like_rewrite_recommendation(item: str) -> bool:
	"""Detect whether a recommendation includes a concrete before/after rewrite."""
	text = item.lower()
	return "rewrite" in text and "->" in text



def _clean_string_list(values: Any) -> list[str]:
	"""Return a sanitized, deduplicated list of meaningful strings."""
	if not isinstance(values, list):
		return []
	filtered = filter_meaningful_keywords([value for value in values if isinstance(value, str)])
	return [keyword for keyword in filtered if normalize_keyword(keyword) not in _GENERIC_POSTING_TERMS]


def _sanitize_report_json(report_json: dict[str, Any]) -> dict[str, Any]:
	"""Remove filler terms from all keyword-bearing sections before persistence."""
	sanitized = dict(report_json)
	highlights = dict(sanitized.get("highlights", {}))
	for key in (
		"common_tools",
		"tool_keywords",
		"common_achievements",
		"matched_keywords",
		"missing_keywords",
		"resume_keywords",
		"posting_keywords",
	):
		highlights[key] = _clean_string_list(highlights.get(key, []))
	sanitized["highlights"] = highlights

	if isinstance(sanitized.get("recommendations"), list):
		sanitized["recommendations"] = [item for item in sanitized["recommendations"] if isinstance(item, str) and item.strip()]

	return sanitized


def _build_recommendations(missing_keywords: list[str], resume_keywords: list[str]) -> list[str]:
	"""Generate actionable resume-edit recommendations with concrete rewrite examples."""
	top_gaps = missing_keywords[:5]
	anchor = resume_keywords[:3]

	if not top_gaps:
		return [
			'Rewrite "Worked on multiple cross-functional projects." -> "Led 4 cross-functional launches with Product, Design, and Engineering, shipping milestones 2 weeks ahead of plan." | Why: adds scope, partners, and measurable impact.',
			'Rewrite "Responsible for improving processes." -> "Redesigned onboarding workflow, reducing handoff time by 32% and improving first-response SLA from 36h to 18h." | Why: replaces vague ownership language with concrete outcomes.',
			"Add one quantified bullet per recent role using this formula: action + tool + scope + measurable result.",
		]

	primary_gap = top_gaps[0]
	secondary_gap = top_gaps[1] if len(top_gaps) > 1 else top_gaps[0]
	anchor_phrase = ", ".join(anchor) if anchor else "your strongest existing skills"

	return [
		f'Rewrite "Experienced with {primary_gap}." -> "Built and maintained {primary_gap} workflows in production, supporting [team/feature] and improving [metric] by [X%]." | Why: converts keyword-only language into credible, ATS-friendly impact evidence.',
		f'Rewrite "Worked with {secondary_gap}." -> "Used {secondary_gap} to deliver [project outcome], collaborating with [stakeholders] and reducing [cost/time/risk] by [X%]." | Why: ties the requirement to business value and collaboration context.',
		f"Add a targeted summary line that bridges {anchor_phrase} to missing requirements ({', '.join(top_gaps[:3])}) so your positioning matches the role language.",
		f"For each missing requirement ({', '.join(top_gaps[:4])}), add one bullet under the most relevant role with this structure: what you built, tool used, scale, and measurable outcome.",
		"Replace weak verbs (helped, worked on, involved in) with ownership verbs (led, built, designed, implemented) and add one metric to every updated bullet.",
	]


def _build_narrative(llm_analysis: dict[str, Any]) -> dict[str, Any]:
	"""Map GPT output fields into the ``narrative`` block stored in the report."""
	return {
		"overview": llm_analysis.get("overview", ""),
		"strengths_summary": llm_analysis.get("strengths_summary", ""),
		"gaps_summary": llm_analysis.get("gaps_summary", ""),
		"resume_experience_level": llm_analysis.get("resume_experience_level", ""),
		"posting_experience_level": llm_analysis.get("posting_experience_level", ""),
	}


def build_report_json(payload: dict[str, Any]) -> dict[str, Any]:
	"""Create the final report JSON artifact from current pipeline payload."""
	job_id = payload.get("job_id")
	if not isinstance(job_id, str) or not job_id:
		raise TypeError("'job_id' must be a non-empty string")

	comparison = payload.get("comparison", {})
	if not isinstance(comparison, dict):
		raise TypeError("'comparison' must be a dict")

	resume_features = payload.get("resume_features", {})
	if not isinstance(resume_features, dict):
		raise TypeError("'resume_features' must be a dict")

	resume_text = payload.get("resume_text", "")
	if not isinstance(resume_text, str):
		raise TypeError("'resume_text' must be a string")

	postings = payload.get("postings", [])
	if not isinstance(postings, list) or not all(isinstance(item, str) for item in postings):
		raise TypeError("'postings' must be a list[str]")

	embedding_features = payload.get("embedding_features", {})
	if not isinstance(embedding_features, dict):
		raise TypeError("'embedding_features' must be a dict")

	llm_analysis = payload.get("llm_analysis")
	llm_available = isinstance(llm_analysis, dict) and bool(llm_analysis)

	match_score = float(comparison.get("match_score", 0.0))
	matched_keywords = list(comparison.get("matched_keywords", []))
	missing_keywords = list(comparison.get("missing_keywords", []))
	resume_keywords = list(comparison.get("resume_keywords", []))
	posting_keywords = list(comparison.get("posting_keywords", []))
	matched_keywords = _filter_report_keywords(matched_keywords)
	missing_keywords = _filter_gap_keywords(missing_keywords)
	resume_keywords = _filter_report_keywords(resume_keywords)
	posting_keywords = _filter_report_keywords(posting_keywords)
	tool_keywords = _extract_tools_from_postings(postings)
	resume_tools = _extract_tools_from_text(resume_text)
	shared_tools = [keyword for keyword in tool_keywords if keyword in set(resume_tools)]
	if shared_tools:
		matched_keywords = _filter_report_keywords([*matched_keywords, *shared_tools])
		missing_keywords = [keyword for keyword in missing_keywords if keyword not in set(shared_tools)]
	if not tool_keywords:
		tool_keywords = _select_tools_from_posting(posting_keywords)
	if not tool_keywords:
		tool_keywords = [keyword for keyword in matched_keywords if normalize_keyword(keyword) in _TOOL_KEYWORDS or normalize_keyword(keyword) in _TECHNICAL_HINTS]
	common_tools = tool_keywords[:12] if tool_keywords else _select_common_tools(posting_keywords, matched_keywords)
	common_achievements = _select_common_achievements(missing_keywords)
	average_similarity = float(embedding_features.get("average_similarity", 0.0))
	match_score = _recompute_match_score(matched_keywords, missing_keywords)
	tool_overlap_score = _compute_tool_overlap_score(tool_keywords, resume_tools)
	# Blend lexical embedding and explicit tool overlap so Fit Overview tracks actual requirement coverage.
	embedding_similarity = round((average_similarity * 0.75) + (tool_overlap_score * 0.25), 3)

	# Use GPT fit label when available; it has richer context than the score threshold.
	if llm_available and llm_analysis.get("overview"):
		fit_label = llm_analysis.get("fit_assessment") or (
			"strong" if match_score >= 0.65 else "moderate" if match_score >= 0.4 else "emerging"
		)
	else:
		fit_label = "strong" if match_score >= 0.65 else "moderate" if match_score >= 0.4 else "emerging"

	# Use LLM-generated recommendations when available; fall back to heuristics.
	if llm_available:
		llm_recs = [r.strip() for r in llm_analysis.get("recommendations", []) if isinstance(r, str) and r.strip()]
		recommendations = llm_recs if llm_recs else _build_recommendations(missing_keywords, resume_keywords)
	else:
		recommendations = _build_recommendations(missing_keywords, resume_keywords)

	# Top up recommendations to ensure at least 5 practical edits, and at least one rewrite example.
	fallback_recs = _build_recommendations(missing_keywords, resume_keywords)
	if not any(_looks_like_rewrite_recommendation(item) for item in recommendations):
		recommendations = [*fallback_recs, *recommendations]

	for candidate in fallback_recs:
		if len(recommendations) >= 5:
			break
		if candidate not in recommendations:
			recommendations.append(candidate)

	# Keep output concise for frontend rendering.
	recommendations = recommendations[:7]

	logger.info(
		"Building report JSON: job_id=%s match_score=%s matched=%d missing=%d embedding_similarity=%s base_embedding=%s tool_overlap=%s llm_available=%s",
		job_id,
		match_score,
		len(matched_keywords),
		len(missing_keywords),
		embedding_similarity,
		average_similarity,
		tool_overlap_score,
		llm_available,
	)

	report_json: dict[str, Any] = {
		"job_id": job_id,
		"summary": {
			"match_score": round(match_score, 3),
			"embedding_similarity": embedding_similarity,
			"fit_label": fit_label,
		},
		"highlights": {
			"common_tools": common_tools,
			"tool_keywords": tool_keywords[:12],
			"common_achievements": common_achievements,
			"matched_keywords": matched_keywords[:15],
			"missing_keywords": missing_keywords[:15],
			"resume_keywords": resume_keywords[:15],
			"posting_keywords": posting_keywords[:15],
			"detected_contact_fields": {
				"emails": resume_features.get("emails", []),
				"phones": resume_features.get("phones", []),
				"links": resume_features.get("links", []),
			},
			"domain_matches": resume_features.get("domain_matches", []),
		},
		"recommendations": recommendations,
	}

	if llm_available:
		report_json["narrative"] = _build_narrative(llm_analysis)

	report_json = _sanitize_report_json(report_json)

	logger.info("Built report JSON: job_id=%s keys=%s llm_available=%s", job_id, sorted(report_json.keys()), llm_available)
	return report_json


def generate_report_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
	"""Attach report JSON to payload for persistence in a downstream task."""
	updated_payload = dict(payload)
	logger.info("Generating report from payload: job_id=%s payload_keys=%s", payload.get("job_id"), sorted(payload.keys()))
	updated_payload["report_json"] = build_report_json(payload)
	logger.info("Generated report payload: job_id=%s report_keys=%s", payload.get("job_id"), sorted(updated_payload["report_json"].keys()))
	return updated_payload