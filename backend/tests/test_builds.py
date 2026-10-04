import asyncio
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import db
from app.main import app
from app.models import Base


def _build_session_factory() -> async_sessionmaker:
    Path("test_build_flow.db").unlink(missing_ok=True)
    engine = create_async_engine("sqlite+aiosqlite:///./test_build_flow.db")

    async def initialize() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(initialize())
    return async_sessionmaker(engine, expire_on_commit=False)


def test_publish_build_captures_equipment_and_computed_stats(monkeypatch) -> None:
    monkeypatch.setattr(db, "session_factory", _build_session_factory())
    client = TestClient(app)
    player = client.post("/dev/player").json()
    cat_id = player["cats"][0]["id"]
    weapon = next(
        item
        for item in client.get(f"/players/{player['id']}/items").json()
        if item["definition"]["slot"] == "weapon"
    )

    equip = client.post(f"/players/{player['id']}/cats/{cat_id}/items/{weapon['id']}/equip")
    assert equip.status_code == 200

    response = client.post(f"/builds/{player['id']}/publish")

    assert response.status_code == 200
    snapshot = response.json()
    assert snapshot["version"] == 1
    assert snapshot["is_current"] is True
    assert snapshot["cat"]["attack"] == 15
    assert [item["instance_id"] for item in snapshot["equipment"]] == [weapon["id"]]

    published = client.get(f"/builds/{player['id']}/published")
    assert published.status_code == 200
    assert published.json()["id"] == snapshot["id"]


def test_republishing_keeps_previous_snapshot_immutable(monkeypatch) -> None:
    monkeypatch.setattr(db, "session_factory", _build_session_factory())
    client = TestClient(app)
    player = client.post("/dev/player").json()

    first = client.post(f"/builds/{player['id']}/publish").json()
    cat_id = player["cats"][0]["id"]
    weapon = next(
        item
        for item in client.get(f"/players/{player['id']}/items").json()
        if item["definition"]["slot"] == "weapon"
    )
    assert client.post(
        f"/players/{player['id']}/cats/{cat_id}/items/{weapon['id']}/equip"
    ).status_code == 200

    second = client.post(f"/builds/{player['id']}/publish").json()

    assert second["version"] == 2
    assert second["id"] != first["id"]
    assert first["cat"]["attack"] == 12
    assert first["equipment"] == []
    assert second["cat"]["attack"] == 15
    assert len(second["equipment"]) == 1


def test_publishing_requires_an_existing_player(monkeypatch) -> None:
    monkeypatch.setattr(db, "session_factory", _build_session_factory())

    client = TestClient(app)
    client.post("/dev/player")
    response = client.post("/builds/missing-player/publish")

    assert response.status_code == 403
