"""Production safety guards: bad config must fail loudly at boot, not silently."""
import pytest

from app.core.config import DEFAULT_SECRET, Settings
from app.core.database import normalize_db_url

GOOD_SECRET = "x" * 48
GOOD_DB = "postgresql://user:pass@host:5432/db"


def test_production_rejects_default_jwt_secret() -> None:
    with pytest.raises(ValueError, match="default value"):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY=DEFAULT_SECRET,
            DATABASE_URL=GOOD_DB,
        )


def test_production_rejects_short_jwt_secret() -> None:
    with pytest.raises(ValueError, match="at least"):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY="tooshort",
            DATABASE_URL=GOOD_DB,
        )


def test_production_rejects_sqlite() -> None:
    with pytest.raises(ValueError, match="SQLite is not supported"):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET_KEY=GOOD_SECRET,
            DATABASE_URL="sqlite:///./inventory.db",
        )


def test_production_accepts_good_config() -> None:
    settings = Settings(
        ENVIRONMENT="production",
        JWT_SECRET_KEY=GOOD_SECRET,
        DATABASE_URL=GOOD_DB,
    )
    assert settings.is_production is True


def test_development_tolerates_defaults() -> None:
    # Local dev must stay frictionless — the guards are production-only.
    settings = Settings(ENVIRONMENT="development", JWT_SECRET_KEY=DEFAULT_SECRET)
    assert settings.is_production is False


def test_cors_origins_parses_comma_separated_list() -> None:
    settings = Settings(FRONTEND_ORIGIN="https://a.com, https://b.com")
    assert settings.cors_origins == ["https://a.com", "https://b.com"]


@pytest.mark.parametrize(
    ("given", "expected"),
    [
        # Neon/Heroku hand out postgres://, which SQLAlchemy 2 rejects outright.
        ("postgres://u:p@h/db", "postgresql+psycopg2://u:p@h/db"),
        ("postgresql://u:p@h/db", "postgresql+psycopg2://u:p@h/db"),
        # Already-explicit driver and SQLite are passed through untouched.
        ("postgresql+psycopg2://u:p@h/db", "postgresql+psycopg2://u:p@h/db"),
        ("sqlite:///./x.db", "sqlite:///./x.db"),
    ],
)
def test_normalize_db_url(given: str, expected: str) -> None:
    assert normalize_db_url(given) == expected
