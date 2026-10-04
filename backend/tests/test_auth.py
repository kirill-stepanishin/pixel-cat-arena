import asyncio
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import db
from app.main import app
from app.models import Base


def _build_session_factory() -> async_sessionmaker:
    Path("test_auth_flow.db").unlink(missing_ok=True)
    engine = create_async_engine("sqlite+aiosqlite:///./test_auth_flow.db")

    async def initialize() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(initialize())
    return async_sessionmaker(engine, expire_on_commit=False)


def test_register_login_me_and_logout(monkeypatch) -> None:
    monkeypatch.setattr(db, "session_factory", _build_session_factory())
    client = TestClient(app)

    registered = client.post(
        "/auth/register",
        json={"username": "auth-player", "password": "correct horse battery staple"},
    )
    assert registered.status_code == 201
    assert registered.json()["username"] == "auth-player"
    assert "session_token" in registered.cookies

    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["id"] == registered.json()["id"]

    assert client.post("/auth/logout").status_code == 204
    assert client.get("/auth/me").status_code == 401

    login = client.post(
        "/auth/login",
        json={"username": "auth-player", "password": "correct horse battery staple"},
    )
    assert login.status_code == 200
    assert client.get("/auth/me").status_code == 200


def test_auth_rejects_duplicate_and_invalid_credentials(monkeypatch) -> None:
    monkeypatch.setattr(db, "session_factory", _build_session_factory())
    client = TestClient(app)
    credentials = {"username": "auth-player", "password": "correct horse battery staple"}

    assert client.post("/auth/register", json=credentials).status_code == 201
    assert client.post("/auth/register", json=credentials).status_code == 409
    assert client.post(
        "/auth/login",
        json={"username": credentials["username"], "password": "wrong password"},
    ).status_code == 401


def test_auth_requires_eight_character_password(monkeypatch) -> None:
    monkeypatch.setattr(db, "session_factory", _build_session_factory())

    response = TestClient(app).post(
        "/auth/register",
        json={"username": "auth-player", "password": "short"},
    )

    assert response.status_code == 422
