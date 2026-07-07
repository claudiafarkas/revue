"""Local JWT authentication helpers for securing API routes."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from api.services.jwt_auth import verify_token

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    """Lightweight authenticated user payload from local JWT token claims."""

    uid: str
    email: str | None


def get_current_user(
    credentials_header: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    """Validate JWT token from Authorization header and return user claims."""
    if credentials_header is None or credentials_header.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header.",
        )

    try:
        claims = verify_token(credentials_header.credentials)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Token verification failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
        ) from exc

    uid = claims.get("sub")
    if not isinstance(uid, str) or not uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token does not include a valid user id.",
        )

    email = claims.get("email")
    return AuthenticatedUser(uid=uid, email=email if isinstance(email, str) else None)