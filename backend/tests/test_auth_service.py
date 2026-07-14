"""Unit tests for the authentication service."""
import pytest
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.services.auth_service import AuthError, AuthService


def _service(db: Session) -> AuthService:
    return AuthService(UserRepository(db))


def _new_user() -> UserCreate:
    return UserCreate(
        email="manager@shop.com",
        full_name="Shop Manager",
        password="supersecret1",
    )


def test_register_creates_user_and_hashes_password(db: Session) -> None:
    service = _service(db)
    user = service.register(_new_user())

    assert user.id is not None
    assert user.email == "manager@shop.com"
    # Password must be stored hashed, never in plaintext.
    assert user.hashed_password != "supersecret1"


def test_register_duplicate_email_raises(db: Session) -> None:
    service = _service(db)
    service.register(_new_user())

    with pytest.raises(AuthError):
        service.register(_new_user())


def test_authenticate_with_correct_password(db: Session) -> None:
    service = _service(db)
    service.register(_new_user())

    user = service.authenticate("manager@shop.com", "supersecret1")
    assert user.email == "manager@shop.com"


def test_authenticate_with_wrong_password_raises(db: Session) -> None:
    service = _service(db)
    service.register(_new_user())

    with pytest.raises(AuthError):
        service.authenticate("manager@shop.com", "wrong-password")


def test_authenticate_unknown_email_raises(db: Session) -> None:
    service = _service(db)

    with pytest.raises(AuthError):
        service.authenticate("nobody@shop.com", "whatever")


def test_issue_token_encodes_user_id(db: Session) -> None:
    service = _service(db)
    user = service.register(_new_user())

    token = service.issue_token(user)
    assert decode_access_token(token) == str(user.id)
