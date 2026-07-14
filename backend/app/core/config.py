"""Application configuration loaded from environment variables."""
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Refusing to boot with this value in production is the point of the check below.
DEFAULT_SECRET = "change-me-to-a-long-random-string"
MIN_SECRET_LENGTH = 32


class Settings(BaseSettings):
    """Central settings object. Values come from the environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # "development" | "production"
    ENVIRONMENT: str = "development"

    # Database
    DATABASE_URL: str = "sqlite:///./inventory.db"

    # JWT
    JWT_SECRET_KEY: str = DEFAULT_SECRET
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # CORS. Comma-separated list of allowed origins. When the frontend is served
    # from the same container (the Docker/HF deployment), this can stay empty —
    # requests are same-origin and never hit CORS.
    FRONTEND_ORIGIN: str = "http://localhost:3000"

    # Directory of the exported frontend. When present, FastAPI serves it.
    STATIC_DIR: str = ""

    # Rate limiting on auth endpoints (requests per minute, per IP).
    AUTH_RATE_LIMIT: str = "10/minute"

    # LLM (optional). When GROQ_API_KEY is unset, agents use template phrasing.
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"

    @property
    def cors_origins(self) -> list[str]:
        """Allowed CORS origins, parsed from the comma-separated setting."""
        return [o.strip() for o in self.FRONTEND_ORIGIN.split(",") if o.strip()]

    @model_validator(mode="after")
    def _guard_production_secrets(self) -> "Settings":
        """Refuse to start in production with an unsafe JWT secret.

        A known/default signing key lets anyone forge a token for any user, so
        this is a hard failure rather than a warning.
        """
        if not self.is_production:
            return self

        if self.JWT_SECRET_KEY == DEFAULT_SECRET:
            raise ValueError(
                "JWT_SECRET_KEY is still the default value. Set a unique random "
                "secret before running in production "
                "(e.g. `python -c \"import secrets; print(secrets.token_urlsafe(48))\"`)."
            )
        if len(self.JWT_SECRET_KEY) < MIN_SECRET_LENGTH:
            raise ValueError(
                f"JWT_SECRET_KEY must be at least {MIN_SECRET_LENGTH} characters "
                f"in production."
            )
        if self.DATABASE_URL.startswith("sqlite"):
            raise ValueError(
                "SQLite is not supported in production (data loss under "
                "concurrency and on ephemeral disks). Set DATABASE_URL to a "
                "PostgreSQL connection string."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
