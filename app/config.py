import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    database_url: str
    session_secret: str
    cookie_secure: bool


def get_settings() -> Settings:
    url = os.getenv("DATABASE_URL", "sqlite:///./fitanalytics.db")
    # Render supplies postgresql://; use psycopg explicitly for SQLAlchemy.
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    secure = os.getenv("COOKIE_SECURE", "false").lower() in {"1", "true", "yes"}
    secret = os.getenv("SESSION_SECRET", "")
    if len(secret) < 32:
        raise RuntimeError("SESSION_SECRET debe tener al menos 32 caracteres")
    return Settings(url, secret, secure)
