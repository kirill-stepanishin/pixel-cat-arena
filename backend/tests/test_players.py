import asyncio

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import db
from app.main import app
from app.models import Base


def _build_session_factory() -> async_sessionmaker:
    engine = create_async_engine("sqlite+aiosqlite:///./test_player_flow.db")

    async def initialize() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(initialize())
    return async_sessionmaker(engine, expire_on_commit=False)


def test_development_player_creation(monkeypatch):
    monkeypatch.setattr(db, "session_factory", _build_session_factory())

    client = TestClient(app)
    response = client.post("/dev/player")

    assert response.status_code == 200
    assert response.json()["username"] == "dev-player"
    payload = response.json()
    assert payload["cats"][0]["name"] == "Mochi"
    assert payload["currencies"][0]["balance"] == 125

    player_id = payload["id"]
    inventory = client.get(f"/players/{player_id}/items")
    assert inventory.status_code == 200
    assert len(inventory.json()) == 4
    sword = next(item for item in inventory.json() if item["definition"]["slot"] == "weapon")
    cat_id = payload["cats"][0]["id"]

    equip = client.post(f"/players/{player_id}/cats/{cat_id}/items/{sword['id']}/equip")
    assert equip.status_code == 200
    assert equip.json()["equipped_cat_id"] == cat_id

    equipped_inventory = client.get(f"/players/{player_id}/items").json()
    equipped_sword = next(item for item in equipped_inventory if item["id"] == sword["id"])
    assert equipped_sword["equipped_cat_id"] == cat_id

    unequip = client.post(f"/players/{player_id}/cats/{cat_id}/items/{sword['id']}/unequip")
    assert unequip.status_code == 200
    assert unequip.json()["equipped_cat_id"] is None

    lookup = client.get(f"/players/{player_id}")
    assert lookup.status_code == 200
    assert lookup.json()["id"] == player_id
