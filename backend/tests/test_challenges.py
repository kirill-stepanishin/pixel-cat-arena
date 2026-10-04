import asyncio
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import db
from app.main import app
from app.models import Base


def _build_session_factory() -> async_sessionmaker:
    Path("test_challenge_flow.db").unlink(missing_ok=True)
    engine = create_async_engine("sqlite+aiosqlite:///./test_challenge_flow.db")

    async def initialize() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(initialize())
    return async_sessionmaker(engine, expire_on_commit=False)


def test_challenge_can_target_username_and_freezes_published_builds(monkeypatch) -> None:
    monkeypatch.setattr(db, "session_factory", _build_session_factory())
    client = TestClient(app)
    challenger = client.post("/players", json={"username": "challenger"}).json()
    challenged = client.post("/players", json={"username": "opponent"}).json()

    first_build = client.post(f"/builds/{challenger['id']}/publish").json()
    opponent_build = client.post(f"/builds/{challenged['id']}/publish").json()
    response = client.post(
        "/pvp/challenges",
        json={
            "challenger_id": challenger["id"],
            "challenged_username": "opponent",
        },
    )

    assert response.status_code == 201
    challenge = response.json()
    assert challenge["status"] == "pending"
    assert challenge["challenger_build"]["id"] == first_build["id"]
    assert challenge["challenged_build"]["id"] == opponent_build["id"]

    lookup = client.get(f"/pvp/challenges/{challenge['id']}")
    assert lookup.status_code == 200
    assert lookup.json()["challenged_id"] == challenged["id"]


def test_challenge_can_target_player_id(monkeypatch) -> None:
    monkeypatch.setattr(db, "session_factory", _build_session_factory())
    client = TestClient(app)
    challenger = client.post("/players", json={"username": "challenger"}).json()
    challenged = client.post("/players", json={"username": "opponent"}).json()
    client.post(f"/builds/{challenger['id']}/publish")
    client.post(f"/builds/{challenged['id']}/publish")

    response = client.post(
        "/pvp/challenges",
        json={
            "challenger_id": challenger["id"],
            "challenged_player_id": challenged["id"],
        },
    )

    assert response.status_code == 201


def test_challenge_requires_both_published_builds_and_rejects_self(monkeypatch) -> None:
    monkeypatch.setattr(db, "session_factory", _build_session_factory())
    client = TestClient(app)
    challenger = client.post("/players", json={"username": "challenger"}).json()
    challenged = client.post("/players", json={"username": "opponent"}).json()

    missing_build = client.post(
        "/pvp/challenges",
        json={
            "challenger_id": challenger["id"],
            "challenged_player_id": challenged["id"],
        },
    )
    assert missing_build.status_code == 409

    self_challenge = client.post(
        "/pvp/challenges",
        json={
            "challenger_id": challenger["id"],
            "challenged_player_id": challenger["id"],
        },
    )
    assert self_challenge.status_code == 400


def test_resolve_challenge_uses_saved_builds_and_is_idempotent(monkeypatch) -> None:
    monkeypatch.setattr(db, "session_factory", _build_session_factory())
    client = TestClient(app)
    challenger = client.post("/players", json={"username": "challenger"}).json()
    challenged = client.post("/players", json={"username": "opponent"}).json()
    challenger_build = client.post(f"/builds/{challenger['id']}/publish").json()
    challenged_build = client.post(f"/builds/{challenged['id']}/publish").json()
    challenge = client.post(
        "/pvp/challenges",
        json={
            "challenger_id": challenger["id"],
            "challenged_player_id": challenged["id"],
        },
    ).json()

    response = client.post(f"/pvp/challenges/{challenge['id']}/resolve")

    assert response.status_code == 200
    match = response.json()
    assert match["challenge_id"] == challenge["id"]
    assert match["result"] in {"challenger", "challenged"}
    assert match["events"]
    assert match["challenger_snapshot"]["attack"] == challenger_build["cat"]["attack"]
    assert match["challenged_snapshot"]["attack"] == challenged_build["cat"]["attack"]

    repeated = client.post(f"/pvp/challenges/{challenge['id']}/resolve")
    assert repeated.status_code == 200
    assert repeated.json() == match
    assert client.get(f"/pvp/challenges/{challenge['id']}").json()["status"] == "completed"

    lookup = client.get(f"/pvp/challenges/{challenge['id']}/match")
    assert lookup.status_code == 200
    assert lookup.json()["id"] == match["id"]


def test_player_history_includes_challenges_and_completed_matches(monkeypatch) -> None:
    monkeypatch.setattr(db, "session_factory", _build_session_factory())
    client = TestClient(app)
    challenger = client.post("/players", json={"username": "challenger"}).json()
    challenged = client.post("/players", json={"username": "opponent"}).json()
    client.post(f"/builds/{challenger['id']}/publish")
    client.post(f"/builds/{challenged['id']}/publish")
    challenge = client.post(
        "/pvp/challenges",
        json={
            "challenger_id": challenger["id"],
            "challenged_player_id": challenged["id"],
        },
    ).json()
    client.post(f"/pvp/challenges/{challenge['id']}/resolve")

    challenger_challenges = client.get(
        f"/pvp/players/{challenger['id']}/challenges"
    )
    challenged_matches = client.get(f"/pvp/players/{challenged['id']}/matches")

    assert challenger_challenges.status_code == 200
    assert [item["id"] for item in challenger_challenges.json()] == [challenge["id"]]
    assert challenged_matches.status_code == 200
    assert len(challenged_matches.json()) == 1
    assert challenged_matches.json()[0]["challenge_id"] == challenge["id"]

    unrelated = client.post("/players", json={"username": "unrelated"}).json()
    assert client.get(f"/pvp/players/{unrelated['id']}/matches").json() == []
