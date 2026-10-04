import asyncio
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import db
from app.main import app
from app.models import Base


def _build_session_factory() -> async_sessionmaker:
    Path("test_market_flow.db").unlink(missing_ok=True)
    engine = create_async_engine("sqlite+aiosqlite:///./test_market_flow.db")

    async def initialize() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(initialize())
    return async_sessionmaker(engine, expire_on_commit=False)


def _register(name: str) -> tuple[TestClient, dict]:
    client = TestClient(app)
    player = client.post("/players", json={"username": name}).json()
    return client, player


def _item(client: TestClient, player: dict, slot: str) -> dict:
    return next(
        item
        for item in client.get(f"/players/{player['id']}/items").json()
        if item["definition"]["slot"] == slot
    )


def _balance(client: TestClient, player: dict) -> int:
    return client.get(f"/players/{player['id']}").json()["currencies"][0]["balance"]


def test_listing_purchase_moves_item_and_coins(monkeypatch) -> None:
    monkeypatch.setattr(db, "session_factory", _build_session_factory())
    seller_client, seller = _register("seller")
    buyer_client, buyer = _register("buyer")
    item = _item(seller_client, seller, "head")
    start_seller, start_buyer = _balance(seller_client, seller), _balance(buyer_client, buyer)

    created = seller_client.post("/marketplace/listings", json={"item_id": item["id"], "price": 40})
    assert created.status_code == 201
    listing = created.json()
    assert listing["status"] == "active" and listing["seller_username"] == "seller"

    assert buyer_client.get("/marketplace/listings").json()[0]["id"] == listing["id"]
    assert seller_client.get("/marketplace/listings").json() == []
    assert len(seller_client.get("/marketplace/listings?scope=mine").json()) == 1

    bought = buyer_client.post(f"/marketplace/listings/{listing['id']}/purchase")
    assert bought.status_code == 200
    assert bought.json()["status"] == "sold" and bought.json()["buyer_id"] == buyer["id"]
    assert _balance(seller_client, seller) == start_seller + 40
    assert _balance(buyer_client, buyer) == start_buyer - 40
    assert item["id"] in [i["id"] for i in buyer_client.get(f"/players/{buyer['id']}/items").json()]
    assert item["id"] not in [i["id"] for i in seller_client.get(f"/players/{seller['id']}/items").json()]

    again = buyer_client.post(f"/marketplace/listings/{listing['id']}/purchase")
    assert again.status_code == 409
    assert buyer_client.get("/marketplace/listings").json() == []


def test_listing_rules_and_filters(monkeypatch) -> None:
    monkeypatch.setattr(db, "session_factory", _build_session_factory())
    seller_client, seller = _register("seller")
    other_client, _ = _register("other")
    cat_id = seller["cats"][0]["id"]
    weapon = _item(seller_client, seller, "weapon")
    head = _item(seller_client, seller, "head")

    seller_client.post(f"/players/{seller['id']}/cats/{cat_id}/items/{weapon['id']}/equip")
    equipped = seller_client.post("/marketplace/listings", json={"item_id": weapon["id"], "price": 10})
    assert equipped.status_code == 409

    assert other_client.post(
        "/marketplace/listings", json={"item_id": head["id"], "price": 10}
    ).status_code == 404
    assert seller_client.post(
        "/marketplace/listings", json={"item_id": head["id"], "price": 0}
    ).status_code == 422

    listing = seller_client.post("/marketplace/listings", json={"item_id": head["id"], "price": 10}).json()
    duplicate = seller_client.post("/marketplace/listings", json={"item_id": head["id"], "price": 12})
    assert duplicate.status_code == 409
    listed_equip = seller_client.post(
        f"/players/{seller['id']}/cats/{cat_id}/items/{head['id']}/equip"
    )
    assert listed_equip.status_code == 409

    assert seller_client.post(f"/marketplace/listings/{listing['id']}/purchase").status_code == 400
    assert len(other_client.get("/marketplace/listings?slot=head").json()) == 1
    assert other_client.get("/marketplace/listings?slot=body").json() == []
    assert other_client.get("/marketplace/listings?rarity=legendary").json() == []


def test_cancel_and_insufficient_funds(monkeypatch) -> None:
    monkeypatch.setattr(db, "session_factory", _build_session_factory())
    seller_client, seller = _register("seller")
    buyer_client, buyer = _register("buyer")
    item = _item(seller_client, seller, "body")
    listing = seller_client.post("/marketplace/listings", json={"item_id": item["id"], "price": 5000}).json()

    broke = buyer_client.post(f"/marketplace/listings/{listing['id']}/purchase")
    assert broke.status_code == 402
    assert _balance(buyer_client, buyer) == 125

    assert buyer_client.post(f"/marketplace/listings/{listing['id']}/cancel").status_code == 403
    cancelled = seller_client.post(f"/marketplace/listings/{listing['id']}/cancel")
    assert cancelled.status_code == 200 and cancelled.json()["status"] == "cancelled"
    assert buyer_client.post(f"/marketplace/listings/{listing['id']}/purchase").status_code == 409
    assert seller_client.post(f"/marketplace/listings/{listing['id']}/cancel").status_code == 409

    relist = seller_client.post("/marketplace/listings", json={"item_id": item["id"], "price": 20})
    assert relist.status_code == 201


def test_marketplace_requires_authentication(monkeypatch) -> None:
    monkeypatch.setattr(db, "session_factory", _build_session_factory())
    assert TestClient(app).get("/marketplace/listings").status_code == 401


def test_instant_sell_rules(monkeypatch) -> None:
    monkeypatch.setattr(db, "session_factory", _build_session_factory())
    client, player = _register("seller")
    items = client.get(f"/players/{player['id']}/items").json()
    head = next(i for i in items if i["definition"]["slot"] == "head")
    assert head["sell_price"] == sum(head["modifiers"].values())

    cat_id = client.get(f"/players/{player['id']}").json()["cats"][0]["id"]
    client.post(f"/players/{player['id']}/cats/{cat_id}/items/{head['id']}/equip")
    assert client.post(f"/players/items/{head['id']}/sell").status_code == 409
    client.post(f"/players/{player['id']}/cats/{cat_id}/items/{head['id']}/unequip")

    sold = client.post(f"/players/items/{head['id']}/sell")
    assert sold.status_code == 200
    assert sold.json()["balance"] == 125 + head["sell_price"]
    assert client.post(f"/players/items/{head['id']}/sell").status_code == 404
    remaining = client.get(f"/players/{player['id']}/items").json()
    assert head["id"] not in [i["id"] for i in remaining]
