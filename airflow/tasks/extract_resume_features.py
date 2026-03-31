"""Extract lightweight structured features from cleaned resume text."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

try:
    from clean_text import clean_text_block
except Exception:  # pragma: no cover - fallback keeps this module importable in varied runtimes.
    _WHITESPACE_RE = re.compile(r"\s+")

    def clean_text_block(raw_text: str, *, keep_line_breaks: bool = True) -> str:
        if not raw_text:
            return ""
        if keep_line_breaks:
            return "\n".join(line.strip() for line in raw_text.splitlines() if line.strip())
        return _WHITESPACE_RE.sub(" ", raw_text).strip()


_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}")
_URL_RE = re.compile(r"(?:https?://|www\.)\S+")
_YEARS_RE = re.compile(r"(\d{1,2})\+?\s+years?", re.IGNORECASE)
_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+.#/-]{1,}")

_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "with",
}

_DEFAULT_HINTS = {
    "transferable": {
        "communication",
        "leadership",
        "analysis",
        "planning",
        "collaboration",
    },
    "domains": {
        "technology": {"python", "sql", "docker", "kubernetes", "aws", "react", "api"},
        "healthcare": {"patient", "clinical", "medical", "hipaa"},
        "finance": {"accounting", "audit", "risk", "valuation"},
        "marketing": {"seo", "campaign", "branding", "content"},
    },
}


def _load_skill_hints() -> dict[str, Any]:
    """Load optional multi-domain hint configuration from local JSON file."""
    config_path = Path(__file__).resolve().parent / "data" / "skill_hints.json"
    if not config_path.exists():
        return _DEFAULT_HINTS

    try:
        config_data = json.loads(config_path.read_text(encoding="utf-8"))
    except Exception:
        return _DEFAULT_HINTS

    transferable_raw = config_data.get("transferable", [])
    domains_raw = config_data.get("domains", {})
    if not isinstance(transferable_raw, list) or not isinstance(domains_raw, dict):
        return _DEFAULT_HINTS

    transferable = {str(item).lower() for item in transferable_raw if isinstance(item, str)}
    domains: dict[str, set[str]] = {}
    for domain_name, hints in domains_raw.items():
        if isinstance(domain_name, str) and isinstance(hints, list):
            domains[domain_name] = {str(item).lower() for item in hints if isinstance(item, str)}

    if not domains and not transferable:
        return _DEFAULT_HINTS

    return {
        "transferable": transferable,
        "domains": domains,
    }


_SKILL_HINTS_CONFIG = _load_skill_hints()


def _tokenize(text: str) -> list[str]:
    tokens = [m.group(0).lower() for m in _TOKEN_RE.finditer(text)]
    return [token for token in tokens if token not in _STOPWORDS and len(token) > 2]


def _detect_domains(tokens: set[str], domain_hints: dict[str, set[str]]) -> list[dict[str, Any]]:
    """Return domains ranked by overlap against configured hint terms."""
    ranked: list[dict[str, Any]] = []
    for domain_name, hints in domain_hints.items():
        if not hints:
            continue
        matched = sorted(tokens & hints)
        if not matched:
            continue
        confidence = len(matched) / len(hints)
        ranked.append(
            {
                "domain": domain_name,
                "confidence": round(confidence, 3),
                "matched_terms": matched,
            }
        )

    ranked.sort(key=lambda item: item["confidence"], reverse=True)
    return ranked


def extract_resume_features(resume_text: str, *, top_keywords: int = 30) -> dict[str, Any]:
    """Return deterministic resume features plus baseline keyword signals."""
    if not isinstance(resume_text, str):
        raise TypeError("resume_text must be a string")

    cleaned_text = clean_text_block(resume_text, keep_line_breaks=True)

    emails = sorted(set(_EMAIL_RE.findall(cleaned_text)))
    phones = sorted(set(_PHONE_RE.findall(cleaned_text)))
    links = sorted(set(_URL_RE.findall(cleaned_text)))

    years = [int(match.group(1)) for match in _YEARS_RE.finditer(cleaned_text)]
    years_experience_max = max(years) if years else None

    token_counts = Counter(_tokenize(cleaned_text))
    keywords = [word for word, _ in token_counts.most_common(top_keywords)]
    keyword_set = set(keywords)

    transferable_hints = _SKILL_HINTS_CONFIG.get("transferable", set())
    domain_hints = _SKILL_HINTS_CONFIG.get("domains", {})

    transferable_skills = sorted(keyword_set & set(transferable_hints))
    domain_matches = _detect_domains(keyword_set, domain_hints)

    domain_specific_skills: list[str] = []
    for match in domain_matches[:3]:
        domain_specific_skills.extend(match["matched_terms"])
    domain_specific_skills = sorted(set(domain_specific_skills))

    skills_detected = sorted(set(transferable_skills + domain_specific_skills))

    return {
        "emails": emails,
        "phones": phones,
        "links": links,
        "years_experience_max": years_experience_max,
        "keywords": keywords,
        "transferable_skills": transferable_skills,
        "domain_matches": domain_matches,
        "skills_detected": skills_detected,
    }


def extract_resume_features_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Attach extracted resume features to a pipeline payload copy."""
    resume_text = payload.get("resume_text", "")
    if not isinstance(resume_text, str):
        raise TypeError("'resume_text' must be a string")

    features = extract_resume_features(resume_text)

    updated_payload = dict(payload)
    updated_payload["resume_text"] = clean_text_block(resume_text, keep_line_breaks=True)
    updated_payload["resume_features"] = features
    return updated_payload