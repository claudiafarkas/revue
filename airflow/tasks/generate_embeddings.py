"""Generate lightweight, deterministic embedding-like vectors for text."""

from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from typing import Any

_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9+.#/-]{1,}")     # token pattern includes common word characters plus some symbols often found in technical terms
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


def _tokenize(text: str) -> list[str]:
    tokens = [m.group(0).lower() for m in _TOKEN_RE.finditer(text)]
    return [token for token in tokens if token not in _STOPWORDS and len(token) > 2]


def _vectorize(text: str, dimensions: int = 128) -> list[float]:
    """Build a stable hashed term-frequency vector for a text string."""
    if dimensions <= 0:
        raise ValueError("dimensions must be greater than zero")

    counts = Counter(_tokenize(text))
    vector = [0.0] * dimensions
    for token, count in counts.items():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        vector[index] += float(count)

    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude > 0:
        vector = [value / magnitude for value in vector]
    return vector


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("Vectors must have the same dimensionality")
    score = sum(x * y for x, y in zip(a, b))        # cosine similarity formula (dot product of a and b)
    return max(0.0, min(1.0, score))


def generate_embedding_features(
    resume_text: str,
    postings: list[str],
    *,
    dimensions: int = 128,
) -> dict[str, Any]:
    """Create embedding features and similarity scores for pipeline use."""
    if not isinstance(resume_text, str):
        raise TypeError("resume_text must be a string")
    if not isinstance(postings, list) or not all(isinstance(item, str) for item in postings):
        raise TypeError("postings must be a list[str]")

    resume_vector = _vectorize(resume_text, dimensions=dimensions)
    posting_vectors = [_vectorize(posting, dimensions=dimensions) for posting in postings]

    similarities = [_cosine_similarity(resume_vector, vector) for vector in posting_vectors]
    average_similarity = sum(similarities) / len(similarities) if similarities else 0.0

    return {
        "dimensions": dimensions,
        "resume_vector": resume_vector,
        "posting_vectors": posting_vectors,
        "similarities": [round(score, 4) for score in similarities],
        "average_similarity": round(average_similarity, 4),
    }


def generate_embeddings_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Attach embedding feature outputs to a pipeline payload copy."""
    postings = payload.get("postings", [])
    resume_text = payload.get("resume_text", "")

    features = generate_embedding_features(resume_text=resume_text, postings=postings)

    updated_payload = dict(payload)
    updated_payload["embedding_features"] = features
    return updated_payload