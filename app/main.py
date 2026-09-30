from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from sqlalchemy import text
from starlette.middleware.sessions import SessionMiddleware

load_dotenv()

from app.config import get_settings  # noqa: E402
from app.db import engine  # noqa: E402
from app.routes import analytics, auth, profile, training  # noqa: E402


def create_app() -> FastAPI:
    config = get_settings()
    app = FastAPI(title="FitAnalytics AI API", version="1.0.0")
    app.add_middleware(SessionMiddleware, secret_key=config.session_secret,
                       same_site="lax", https_only=config.cookie_secure, max_age=60 * 60 * 24 * 7)
    app.include_router(auth.router)
    app.include_router(profile.router)
    app.include_router(training.router)
    app.include_router(analytics.router)

    @app.get("/api/salud", tags=["Sistema"])
    def health():
        with engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"estado": "ok"}

    return app


app = create_app()
