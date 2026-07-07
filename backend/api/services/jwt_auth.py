"""JWT token generation and verification for local authentication."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


def _get_jwt_secret() -> str:
    """Get JWT secret key from environment or use default for local development."""
    secret = os.getenv("JWT_SECRET", "local-dev-secret-change-in-production").strip()
    if secret == "local-dev-secret-change-in-production":
        logger.warning("Using default JWT secret key — change JWT_SECRET in production!")
    return secret


def _get_jwt_algorithm() -> str:
    """Get JWT algorithm from environment or use default."""
    return os.getenv("JWT_ALGORITHM", "HS256").strip()


def generate_token(user_id: str, email: str | None = None, expires_in_hours: int = 24) -> str:
    """
    Generate a JWT token for a user.
    
    Args:
        user_id: Unique user identifier (UUID or similar)
        email: Optional user email
        expires_in_hours: Token expiration time in hours (default 24)
    
    Returns:
        Encoded JWT token string
    """
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=expires_in_hours)
    
    payload: dict[str, Any] = {
        "sub": user_id,
        "iat": now,
        "exp": expires_at,
    }
    
    if email:
        payload["email"] = email
    
    token = jwt.encode(
        payload,
        _get_jwt_secret(),
        algorithm=_get_jwt_algorithm(),
    )
    
    logger.info("Generated JWT token for user_id=%s expires_at=%s", user_id, expires_at)
    return token


def verify_token(token: str) -> dict[str, Any]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
    
    Returns:
        Decoded token claims
    
    Raises:
        HTTPException: If token is invalid, expired, or malformed
    """
    try:
        payload = jwt.decode(
            token,
            _get_jwt_secret(),
            algorithms=[_get_jwt_algorithm()],
        )
        return payload
    except jwt.ExpiredSignatureError as exc:
        logger.warning("Token verification failed: token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
        ) from exc
    except jwt.InvalidTokenError as exc:
        logger.warning("Token verification failed: invalid token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or malformed token.",
        ) from exc
    except Exception as exc:
        logger.exception("Unexpected error during token verification")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token verification failed.",
        ) from exc
