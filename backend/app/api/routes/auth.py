"""Authentication routes: register, login, current user."""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import get_auth_service, get_current_user
from app.core.config import settings
from app.core.limiter import limiter
from app.models.user import User
from app.schemas.auth import AuthResponse, LoginRequest
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import AuthError, AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit(settings.AUTH_RATE_LIMIT)
def register(
    request: Request,  # required by slowapi to identify the caller
    payload: UserCreate,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """Register a new user and return an access token."""
    try:
        user = service.register(payload)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=exc.message
        ) from exc

    token = service.issue_token(user)
    return AuthResponse(access_token=token, user=UserRead.model_validate(user))


@router.post("/login", response_model=AuthResponse)
@limiter.limit(settings.AUTH_RATE_LIMIT)
def login(
    request: Request,  # required by slowapi to identify the caller
    payload: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """Authenticate with email + password and return an access token."""
    try:
        user = service.authenticate(payload.email, payload.password)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message
        ) from exc

    token = service.issue_token(user)
    return AuthResponse(access_token=token, user=UserRead.model_validate(user))


@router.post("/token", response_model=AuthResponse, include_in_schema=False)
def login_form(
    form: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """OAuth2 password-flow endpoint (used by Swagger UI Authorize button)."""
    try:
        user = service.authenticate(form.username, form.password)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message
        ) from exc

    token = service.issue_token(user)
    return AuthResponse(access_token=token, user=UserRead.model_validate(user))


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    """Return the currently authenticated user."""
    return UserRead.model_validate(current_user)
