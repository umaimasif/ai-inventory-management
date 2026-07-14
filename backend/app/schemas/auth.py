"""Pydantic schemas for authentication."""
from pydantic import BaseModel, EmailStr

from app.schemas.user import UserRead


class LoginRequest(BaseModel):
    """Credentials for logging in."""

    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT access token response."""

    access_token: str
    token_type: str = "bearer"


class AuthResponse(BaseModel):
    """Token plus the authenticated user's public data."""

    access_token: str
    token_type: str = "bearer"
    user: UserRead
