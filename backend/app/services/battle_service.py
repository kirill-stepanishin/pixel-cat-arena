from __future__ import annotations

import random
import secrets
from fractions import Fraction

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.battle import Battle, BattleEvent, Enemy
from app.models.item import ItemInstance
from app.models.player import Player

ENEMY_DEFINITIONS = (
    {"id": "dummy-1", "name": "Dummy 1", "visual_key": "dummy-1", "attack": 7, "defense": 8, "speed": 6},
    {"id": "dummy-2", "name": "Dummy 2", "visual_key": "dummy-2", "attack": 11, "defense": 12, "speed": 7},
    {"id": "dummy-3", "name": "Dummy 3", "visual_key": "dummy-3", "attack": 15, "defense": 16, "speed": 8},
)
MAX_TURNS = 100
MAX_HP = 100


async def ensure_enemy_roster(session: AsyncSession) -> list[Enemy]:
    result = await session.execute(select(Enemy).where(Enemy.id.in_([item["id"] for item in ENEMY_DEFINITIONS])))
    existing = {enemy.id: enemy for enemy in result.scalars().all()}
    missing = [
        Enemy(**definition)
        for definition in ENEMY_DEFINITIONS
        if definition["id"] not in existing
    ]
    if missing:
        session.add_all(missing)
        await session.flush()
        existing.update({enemy.id: enemy for enemy in missing})
    return [existing[definition["id"]] for definition in ENEMY_DEFINITIONS]


async def get_current_enemy(session: AsyncSession, player_id: str) -> Enemy | None:
    player = await session.get(Player, player_id, with_for_update=True)
    if player is None:
        return None
    roster = await ensure_enemy_roster(session)
    if player.current_enemy_id not in {enemy.id for enemy in roster}:
        player.current_enemy_id = roster[0].id
        await session.flush()
    return next(enemy for enemy in roster if enemy.id == player.current_enemy_id)


async def create_pve_battle(
    session: AsyncSession,
    player_id: str,
    *,
    seed: int | None = None,
) -> Battle | None:
    player_result = await session.execute(
        select(Player)
        .options(
            selectinload(Player.cats),
            selectinload(Player.items).selectinload(ItemInstance.definition),
        )
        .where(Player.id == player_id)
    )
    player = player_result.scalar_one_or_none()
    if player is None or not player.cats:
        return None

    player = await session.get(Player, player_id, with_for_update=True)
    if player is None:
        return None
    enemy = await get_current_enemy(session, player_id)
    if enemy is None:
        return None
    cat = player.cats[0]
    equipped_items = [item for item in player.items if item.equipped_cat_id == cat.id]
    modifiers = {
        "attack": sum(item.definition.modifiers.get("attack", 0) for item in equipped_items),
        "defense": sum(item.definition.modifiers.get("defense", 0) for item in equipped_items),
        "speed": sum(item.definition.modifiers.get("speed", 0) for item in equipped_items),
    }
    player_snapshot = {
        "name": cat.name,
        "attack": cat.attack + modifiers["attack"],
        "defense": cat.defense + modifiers["defense"],
        "speed": max(1, cat.speed + modifiers["speed"]),
        "max_hp": MAX_HP,
        "visual_key": "mochi",
    }
    enemy_snapshot = {
        "name": enemy.name,
        "attack": enemy.attack,
        "defense": enemy.defense,
        "speed": max(1, enemy.speed),
        "max_hp": MAX_HP,
        "visual_key": enemy.visual_key,
    }
    battle_seed = seed if seed is not None else secrets.randbits(63)
    result, events = resolve_battle(player_snapshot, enemy_snapshot, battle_seed)
    battle = Battle(
        player_id=player_id,
        enemy_id=enemy.id,
        seed=battle_seed,
        status="completed",
        result=result,
        player_snapshot=player_snapshot,
        enemy_snapshot=enemy_snapshot,
        turn_count=sum(event["event_type"] == "attack" for event in events),
        events=[BattleEvent(**event) for event in events],
    )
    session.add(battle)
    if result == "player":
        roster = await ensure_enemy_roster(session)
        current_index = next(index for index, item in enumerate(roster) if item.id == enemy.id)
        player.current_enemy_id = roster[min(current_index + 1, len(roster) - 1)].id
    await session.flush()
    await session.refresh(battle, attribute_names=["events"])
    return battle


def resolve_battle(
    player: dict[str, object],
    enemy: dict[str, object],
    seed: int,
) -> tuple[str, list[dict[str, object]]]:
    rng = random.Random(seed)
    player_hp = MAX_HP
    enemy_hp = MAX_HP
    player_next_attack = Fraction(0)
    enemy_next_attack = Fraction(0)
    events: list[dict[str, object]] = []

    for turn_number in range(1, MAX_TURNS + 1):
        if player_next_attack < enemy_next_attack:
            attacker = "player"
            player_next_attack += Fraction(1, int(player["speed"]))
            defender_attack = enemy
        elif enemy_next_attack < player_next_attack:
            attacker = "enemy"
            enemy_next_attack += Fraction(1, int(enemy["speed"]))
            defender_attack = player
        else:
            attacker = "player" if rng.randrange(2) == 0 else "enemy"
            if attacker == "player":
                player_next_attack += Fraction(1, int(player["speed"]))
                defender_attack = enemy
            else:
                enemy_next_attack += Fraction(1, int(enemy["speed"]))
                defender_attack = player

        attacker_data = player if attacker == "player" else enemy
        damage = max(1, int(attacker_data["attack"]) - int(defender_attack["defense"]) // 2)
        if attacker == "player":
            enemy_hp = max(0, enemy_hp - damage)
        else:
            player_hp = max(0, player_hp - damage)
        elapsed = float(min(player_next_attack, enemy_next_attack))
        events.append(
            {
                "sequence": turn_number,
                "turn_number": turn_number,
                "event_type": "attack",
                "attacker": attacker,
                "damage": damage,
                "player_hp": player_hp,
                "enemy_hp": enemy_hp,
                "elapsed_time": elapsed,
            }
        )
        if enemy_hp == 0 or player_hp == 0:
            winner = "player" if enemy_hp == 0 else "enemy"
            events.append(
                {
                    "sequence": turn_number + 1,
                    "turn_number": turn_number,
                    "event_type": "victory" if winner == "player" else "defeat",
                    "attacker": winner,
                    "damage": 0,
                    "player_hp": player_hp,
                    "enemy_hp": enemy_hp,
                    "elapsed_time": elapsed,
                }
            )
            return winner, events

    events.append(
        {
            "sequence": MAX_TURNS + 1,
            "turn_number": MAX_TURNS,
            "event_type": "draw",
            "attacker": None,
            "damage": 0,
            "player_hp": player_hp,
            "enemy_hp": enemy_hp,
            "elapsed_time": float(min(player_next_attack, enemy_next_attack)),
        }
    )
    return "draw", events


async def get_battle(session: AsyncSession, battle_id: str) -> Battle | None:
    result = await session.execute(
        select(Battle)
        .options(selectinload(Battle.events))
        .where(Battle.id == battle_id)
    )
    return result.scalar_one_or_none()
