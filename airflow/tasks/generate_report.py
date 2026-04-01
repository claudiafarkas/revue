"""Assemble a structured report payload from pipeline outputs."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

_GENERIC_POSTING_TERMS = {
	"across",
	"advantage",
	"analytics",
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
	"driven",
	"engineer",
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
	"aws",
	"azure",
	"bigquery",
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
	"warehouse",
}


def _filter_report_keywords(keywords: list[str]) -> list[str]:
	"""Remove generic language so report sections use only meaningful keywords."""
	seen: set[str] = set()
	filtered: list[str] = []
	for keyword in keywords:
		cleaned = keyword.strip().lower()
		if not cleaned or cleaned in seen or cleaned in _GENERIC_POSTING_TERMS:
			continue
		if len(cleaned) <= 2:
			continue
		seen.add(cleaned)
		filtered.append(cleaned)
	return filtered


def _select_common_tools(posting_keywords: list[str], matched_keywords: list[str]) -> list[str]:
	"""Favor technical or tool-like terms over generic recruiting language."""
	candidates = _filter_report_keywords(posting_keywords + [keyword for keyword in matched_keywords if keyword not in posting_keywords])
	preferred = [keyword for keyword in candidates if keyword in _TOOL_KEYWORDS or any(char in keyword for char in ("/", "+", ".", "#", "-"))]
	ordered = preferred if preferred else candidates
	return ordered[:12]


def _select_common_achievements(missing_keywords: list[str]) -> list[str]:
	"""Return filtered achievement and emphasis gaps without filler words."""
	return _filter_report_keywords(missing_keywords)[:12]


def _looks_like_rewrite_recommendation(item: str) -> bool:
	"""Detect whether a recommendation includes a concrete before/after rewrite."""
	text = item.lower()
	return "rewrite" in text and "->" in text


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
	common_tools = _select_common_tools(posting_keywords, matched_keywords)
	common_achievements = _select_common_achievements(missing_keywords)
	average_similarity = float(embedding_features.get("average_similarity", 0.0))

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
		"Building report JSON: job_id=%s match_score=%s matched=%d missing=%d embedding_similarity=%s llm_available=%s",
		job_id,
		match_score,
		len(matched_keywords),
		len(missing_keywords),
		average_similarity,
		llm_available,
	)

	report_json: dict[str, Any] = {
		"job_id": job_id,
		"summary": {
			"match_score": round(match_score, 3),
			"embedding_similarity": round(average_similarity, 3),
			"fit_label": fit_label,
		},
		"highlights": {
			"common_tools": common_tools,
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

	logger.info("Built report JSON: job_id=%s keys=%s llm_available=%s", job_id, sorted(report_json.keys()), llm_available)
	return report_json


def generate_report_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
	"""Attach report JSON to payload for persistence in a downstream task."""
	updated_payload = dict(payload)
	logger.info("Generating report from payload: job_id=%s payload_keys=%s", payload.get("job_id"), sorted(payload.keys()))
	updated_payload["report_json"] = build_report_json(payload)
	logger.info("Generated report payload: job_id=%s report_keys=%s", payload.get("job_id"), sorted(updated_payload["report_json"].keys()))
	return updated_payload