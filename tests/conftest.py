import os

os.environ.setdefault("SESSION_SECRET", "test-secret-with-more-than-thirty-two-characters")

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from app.db import engine
from app.main import create_app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("COOKIE_SECURE", "false")
    engine.cache_clear()
    command.upgrade(Config("alembic.ini"), "head")
    with TestClient(create_app()) as test_client:
        yield test_client
    engine.cache_clear()


def token(client):
    return client.get("/api/auth/csrf").json()["csrf_token"]


def register(client, email="ana@example.com"):
    response = client.post("/api/auth/registro", headers={"X-CSRF-Token": token(client)}, json={
        "nombre": "Ana Demo", "correo": email, "clave": "UnSecretoLargo123!"})
    assert response.status_code == 201, response.text
    return response.json()["csrf_token"]


def profile(client, csrf):
    response = client.put("/api/perfil/datos", headers={"X-CSRF-Token": csrf}, json={
        "edad": 25, "talla_m": 1.75, "peso_kg": 80, "objetivo": "Aumentar mi fuerza"})
    assert response.status_code == 200, response.text
    return response.json()
