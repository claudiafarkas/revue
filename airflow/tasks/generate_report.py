"""Assemble a structured report payload from pipeline outputs."""

from __future__ import annotations

from typing import Any


def _build_recommendations(missing_keywords: list[str]) -> list[str]:
	"""Generate concise recommendations based on missing keywords."""
	if not missing_keywords:
		return ["Your resume already reflects many target job requirements. Tailor examples for each application."]

	top_gaps = missing_keywords[:5]
	recommendations = [
		"Add evidence-backed bullet points for these recurring requirements: " + ", ".join(top_gaps) + ".",
		"Prioritize measurable outcomes and context (scope, impact, tools) in experience bullets.",
		"Update summary and skills sections to match target role language while staying truthful.",
	]
	return recommendations


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

	match_score = float(comparison.get("match_score", 0.0))
	matched_keywords = list(comparison.get("matched_keywords", []))
	missing_keywords = list(comparison.get("missing_keywords", []))
	average_similarity = float(embedding_features.get("average_similarity", 0.0))

	report_json = {
		"job_id": job_id,
		"summary": {
			"match_score": round(match_score, 3),
			"embedding_similarity": round(average_similarity, 3),
			"fit_label": "strong" if match_score >= 0.65 else "moderate" if match_score >= 0.4 else "emerging",
		},
		"highlights": {
			"matched_keywords": matched_keywords[:15],
			"missing_keywords": missing_keywords[:15],
			"detected_contact_fields": {
				"emails": resume_features.get("emails", []),
				"phones": resume_features.get("phones", []),
				"links": resume_features.get("links", []),
			},
			"domain_matches": resume_features.get("domain_matches", []),
		},
		"recommendations": _build_recommendations(missing_keywords),
	}
	return report_json


def generate_report_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
	"""Attach report JSON to payload for persistence in a downstream task."""
	updated_payload = dict(payload)
	updated_payload["report_json"] = build_report_json(payload)
	return updated_payload