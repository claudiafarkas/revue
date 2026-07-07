"""Authentication routes for user registration, login, and logout."""

from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass

import psycopg
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from api.services.database import connection_string
from api.services.jwt_auth import generate_token, verify_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    """Schema for user signup request."""

    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """Schema for user login request."""

    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    """Schema for auth response with token and user info."""

    access_token: str
    user_id: str
    email: str


@dataclass(frozen=True)
class LocalUser:
    """Lightweight local user payload."""

    user_id: str
    email: str


def _hash_password(password: str) -> str:
    """
    Hash a password using a simple method (for local dev only!).
    In production, use bcrypt or similar.
    """
    import hashlib

    return hashlib.sha256(password.encode()).hexdigest()


def _verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return _hash_password(password) == hashed


def _create_users_table_if_not_exists() -> None:
    """Ensure users table exists."""
    try:
        with psycopg.connect(connection_string()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        email TEXT NOT NULL UNIQUE,
                        password_hash TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
                    """
                )
                conn.commit()
        logger.info("Ensured users table exists")
    except Exception as exc:
        logger.exception("Failed to create users table")
        raise RuntimeError("Failed to initialize auth table") from exc


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def signup(request: SignupRequest) -> AuthResponse:
    """
    Register a new user with email and password.
    
    Returns:
        AuthResponse with JWT token and user info
    """
    _create_users_table_if_not_exists()

    email_lower = request.email.lower().strip()
    password_hash = _hash_password(request.password)
    user_id = str(uuid.uuid4())

    try:
        with psycopg.connect(connection_string()) as conn:
            with conn.cursor() as cur:
                # Check if user already exists
                cur.execute("SELECT user_id FROM users WHERE email = %s", (email_lower,))
                if cur.fetchone():
                    logger.warning("Signup attempted for existing email: %s", email_lower)
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="User with this email already exists.",
                    )

                # Create new user
                cur.execute(
                    "INSERT INTO users (user_id, email, password_hash) VALUES (%s, %s, %s)",
                    (user_id, email_lower, password_hash),
                )
                conn.commit()

        logger.info("User registered: email=%s user_id=%s", email_lower, user_id)

        token = generate_token(user_id, email_lower)
        return AuthResponse(
            access_token=token,
            user_id=user_id,
            email=email_lower,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Signup failed for email=%s", email_lower)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Signup failed.",
        ) from exc


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest) -> AuthResponse:
    """
    Authenticate user with email and password.
    
    Returns:
        AuthResponse with JWT token and user info
    """
    _create_users_table_if_not_exists()

    email_lower = request.email.lower().strip()

    try:
        with psycopg.connect(connection_string()) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT user_id, password_hash FROM users WHERE email = %s",
                    (email_lower,),
                )
                row = cur.fetchone()

        if not row:
            logger.warning("Login attempted with non-existent email: %s", email_lower)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        user_id, password_hash = row

        if not _verify_password(request.password, password_hash):
            logger.warning("Login failed for email=%s due to invalid password", email_lower)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
            )

        logger.info("User logged in: email=%s user_id=%s", email_lower, user_id)

        token = generate_token(user_id, email_lower)
        return AuthResponse(
            access_token=token,
            user_id=user_id,
            email=email_lower,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Login failed for email=%s", email_lower)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed.",
        ) from exc
