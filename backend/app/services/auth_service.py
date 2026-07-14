"""Authentication business logic. Sits between routes and repositories."""
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class AuthError(Exception):
    """Raised for expected auth failures (mapped to HTTP errors in the route)."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AuthService:
    """Handles registration, login, and token issuance."""

    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def register(self, data: UserCreate) -> User:
        """Create a new user. Raises AuthError if the email is taken."""
        if self._users.get_by_email(data.email):
            raise AuthError("Email already registered")

        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=hash_password(data.password),
        )
        return self._users.create(user)

    def authenticate(self, email: str, password: str) -> User:
        """Validate credentials and return the user. Raises AuthError on failure."""
        user = self._users.get_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise AuthError("Invalid email or password")
        if not user.is_active:
            raise AuthError("User account is inactive")
        return user

    @staticmethod
    def issue_token(user: User) -> str:
        """Create an access token for an authenticated user."""
        return create_access_token(subject=user.id)
