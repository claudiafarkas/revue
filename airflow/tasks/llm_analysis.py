"""LLM-powered skill extraction and narrative report generation using Gemini.

Replaces the heuristic token-frequency comparison with a gemini-2.0-flash call that:
  1. Extracts real skills / tools / requirements from both resume and postings.
  2. Matches them semantically (handles synonyms and close equivalents).
  3. Produces analyst-grade narrative paragraphs and specific recommendations.

The module degrades gracefully — if the ``google-genai`` package is not installed or
``GEMINI_API_KEY`` is not set the pipeline continues unchanged using the
heuristic results from compare_resume.

Get a free API key at https://aistudio.google.com (no billing required for the free tier).
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

_MAX_RESUME_CHARS = 4000
_MAX_POSTINGS_CHARS = 6000

_SYSTEM_PROMPT = """\
You are a precise, professional resume analyst with deep expertise in talent acquisition.
When given a resume and one or more job postings you extract skills accurately and write
concise analyst-grade narrative summaries.
Always respond with valid JSON only — no markdown fences, no extra explanation.\
"""

_USER_PROMPT_TEMPLATE = """\
Analyze the resume and job postings below. Return a single JSON object with \
exactly these keys:

{{
  "resume_skills": [...],
  "posting_requirements": [...],
  "matched_skills": [...],
  "missing_skills": [...],
  "resume_experience_level": "junior|mid|senior|principal",
  "posting_experience_level": "junior|mid|senior|principal",
  "overview": "3-4 sentence analyst-grade overall assessment of fit.",
  "strengths_summary": "2-3 sentences on what the candidate does well relative to these roles.",
  "gaps_summary": "2-3 sentences on gaps or under-represented experience.",
  "recommendations": [
        "Rewrite \"<actual resume phrase>\" -> \"<improved resume bullet>\" | Why: <short rationale tied to posting requirements>",
        "Rewrite \"<actual resume phrase>\" -> \"<improved resume bullet>\" | Why: <short rationale tied to posting requirements>",
        "Rewrite \"<actual resume phrase>\" -> \"<improved resume bullet>\" | Why: <short rationale tied to posting requirements>",
        "Add bullet under <section>: \"<new bullet with tool + scope + metric>\" | Why: <gap addressed>",
        "Add targeted summary line: \"<summary line aligned with role language>\" | Why: <fit improvement>"
  ]
}}

Field definitions:
- resume_skills: every specific skill, tool, technology, certification, or qualification found in the resume.
- posting_requirements: every specific skill, tool, or requirement extracted from the job postings (deduplicated across all postings).
- matched_skills: skills clearly present in the resume that address a job requirement — allow synonyms and close equivalents (e.g. "Postgres" matches "relational databases").
- missing_skills: requirements from the postings not adequately represented in the resume.
- overview / strengths_summary / gaps_summary: written for the candidate, professional tone, specific to the actual content.
- recommendations: highly specific resume edits referencing real gaps from the analysis — NOT generic advice.
    - At least 3 recommendations must be explicit before/after rewrites in this exact style:
        Rewrite "<actual phrase from resume>" -> "<improved phrase>" | Why: <reason>
    - Use phrases that actually appear in the resume when possible; avoid inventing technologies not present in resume or postings.
    - Keep each recommendation to 1-2 sentences max.

RESUME:
{resume}

JOB POSTINGS:
{postings}\
"""


def _build_prompt(resume_text: str, postings: list[str]) -> str:
    combined_postings = "\n---\n".join(postings)[:_MAX_POSTINGS_CHARS]
    resume_snippet = resume_text[:_MAX_RESUME_CHARS]
    return _USER_PROMPT_TEMPLATE.format(resume=resume_snippet, postings=combined_postings)


def analyze_with_llm(payload: dict[str, Any]) -> dict[str, Any]:
    """Run Gemini-based skill extraction and narrative generation.

    Returns an enriched copy of ``payload`` with two new keys:
    - ``llm_analysis``: raw structured output from Gemini.
    - ``comparison``: patched in-place with LLM-quality skill lists and a
      recalculated ``match_score``.

    If the call cannot be made (missing package/key, API error) the original
    payload is returned unmodified so downstream heuristic steps still run.
    """
    try:
        from google import genai  # lazy — keeps module importable without google-genai
        from google.genai import types as genai_types
    except ImportError:
        logger.warning("google-genai package not installed; skipping LLM analysis")
        return payload

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY not set; skipping LLM analysis")
        return payload

    resume_text = payload.get("resume_text", "")
    postings = payload.get("postings", [])

    if not isinstance(resume_text, str) or not resume_text.strip():
        logger.warning("Empty resume_text; skipping LLM analysis")
        return payload
    if not isinstance(postings, list) or not postings:
        logger.warning("No postings available; skipping LLM analysis")
        return payload

    client = genai.Client(api_key=api_key)
    full_prompt = _SYSTEM_PROMPT + "\n\n" + _build_prompt(resume_text, postings)

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt,
            config=genai_types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.15,
                max_output_tokens=1800,
            ),
        )
        raw = response.text or "{}"
        result: dict[str, Any] = json.loads(raw)
    except Exception:
        logger.exception("LLM analysis call failed; falling back to heuristic pipeline")
        return payload

    if not isinstance(result, dict):
        logger.error("LLM returned a non-dict response; skipping LLM analysis")
        return payload

    llm_matched = [s for s in result.get("matched_skills", []) if isinstance(s, str)]
    llm_missing = [s for s in result.get("missing_skills", []) if isinstance(s, str)]
    llm_posting_reqs = [s for s in result.get("posting_requirements", []) if isinstance(s, str)]
    llm_resume_skills = [s for s in result.get("resume_skills", []) if isinstance(s, str)]

    logger.info(
        "Gemini analysis complete: job_id=%s matched=%d missing=%d resume_skills=%d posting_requirements=%d",
        payload.get("job_id"),
        len(llm_matched),
        len(llm_missing),
        len(llm_resume_skills),
        len(llm_posting_reqs),
    )

    updated_payload = dict(payload)
    updated_payload["llm_analysis"] = result

    # Patch the comparison dict with LLM-quality skill lists and recalculate score.
    comparison = dict(payload.get("comparison", {}))
    if llm_matched or llm_missing:
        denominator = max(len(llm_posting_reqs), len(llm_matched) + len(llm_missing), 1)
        comparison["matched_keywords"] = llm_matched
        comparison["missing_keywords"] = llm_missing
        comparison["posting_keywords"] = llm_posting_reqs
        comparison["resume_keywords"] = llm_resume_skills
        comparison["match_score"] = round(len(llm_matched) / denominator, 3)
        updated_payload["comparison"] = comparison

    return updated_payload
