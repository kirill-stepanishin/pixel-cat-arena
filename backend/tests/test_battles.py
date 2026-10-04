import asyncio

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import db
from app.main import app
from app.models import Base
from app.services.battle_service import MAX_TURNS, resolve_battle


def _build_session_factory() -> async_sessionmaker:
    engine = create_async_engine("sqlite+aiosqlite:///./test_battle_flow.db")

    async def initialize() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    asyncio.run(initialize())
    return async_sessionmaker(engine, expire_on_commit=False)


def _combatant(attack: int, defense: int, speed: int) -> dict[str, object]:
    return {
        "name": "fighter",
        "attack": attack,
        "defense": defense,
        "speed": speed,
        "max_hp": 100,
        "visual_key": "fighter",
    }


def test_battle_resolution_is_deterministic_and_uses_fixed_hp() -> None:
    player = _combatant(12, 10, 8)
    enemy = _combatant(7, 8, 6)

    first_result = resolve_battle(player, enemy, seed=42)
    second_result = resolve_battle(player, enemy, seed=42)

    assert first_result == second_result
    assert first_result[1][0]["player_hp"] == 100
    assert first_result[1][0]["enemy_hp"] < 100
    assert first_result[0] in {"player", "enemy", "draw"}


def test_faster_attacker_gets_more_attacks_over_time() -> None:
    player = _combatant(1, 100, 10)
    enemy = _combatant(1, 100, 1)

    _, events = resolve_battle(player, enemy, seed=1)

    player_attacks = sum(
        event["event_type"] == "attack" and event["attacker"] == "player"
        for event in events
    )
    enemy_attacks = sum(
        event["event_type"] == "attack" and event["attacker"] == "enemy"
        for event in events
    )
    assert player_attacks > enemy_attacks


def test_turn_limit_is_a_draw() -> None:
    player = _combatant(1, 1000, 10)
    enemy = _combatant(1, 1000, 10)

    result, events = resolve_battle(player, enemy, seed=1)

    assert result == "draw"
    assert len([event for event in events if event["event_type"] == "attack"]) == MAX_TURNS
    assert events[-1]["event_type"] == "draw"


def test_pve_endpoint_persists_battle_and_events(monkeypatch) -> None:
    monkeypatch.setattr(db, "session_factory", _build_session_factory())
    client = TestClient(app)

    player = client.post("/dev/player").json()
    response = client.post("/battles/pve", json={"player_id": player["id"]})

    assert response.status_code == 200
    battle = response.json()
    assert battle["enemy_id"] == "training-dummy"
    assert battle["player_snapshot"]["max_hp"] == 100
    assert battle["enemy_snapshot"]["max_hp"] == 100
    assert battle["events"]

    lookup = client.get(f"/battles/{battle['id']}")
    assert lookup.status_code == 200
    assert lookup.json()["seed"] == battle["seed"]


def test_pve_rejects_unknown_player(monkeypatch) -> None:
    monkeypatch.setattr(db, "session_factory", _build_session_factory())
    response = TestClient(app).post(
        "/battles/pve",
        json={"player_id": "missing-player"},
    )

    assert response.status_code == 404
