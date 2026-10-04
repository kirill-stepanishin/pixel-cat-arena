from __future__ import annotations

import random
import secrets
from fractions import Fraction

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.battle import Battle, BattleEvent, Enemy, Reward
from app.models.item import ItemDefinition, ItemInstance
from app.models.player import Currency, Player

BASE_ENEMY = {"attack": 7, "defense": 8, "speed": 6}
ENEMY_STAGE_GROWTH = {"attack": 4, "defense": 4, "speed": 1}
COINS_PER_STAGE = 25
MAX_TURNS = 100
MAX_HP = 100


def enemy_definition(stage: int) -> dict[str, object]:
    return {
        "id": f"dummy-{stage}",
        "stage": stage,
        "name": f"Dummy {stage}",
        "visual_key": "dummy-1",
        "attack": BASE_ENEMY["attack"] + ENEMY_STAGE_GROWTH["attack"] * (stage - 1),
        "defense": BASE_ENEMY["defense"] + ENEMY_STAGE_GROWTH["defense"] * (stage - 1),
        "speed": BASE_ENEMY["speed"] + ENEMY_STAGE_GROWTH["speed"] * (stage - 1),
    }


async def ensure_enemy(session: AsyncSession, stage: int) -> Enemy:
    result = await session.execute(select(Enemy).where(Enemy.stage == stage))
    enemy = result.scalar_one_or_none()
    if enemy is None:
        enemy = Enemy(**enemy_definition(stage))
        session.add(enemy)
        await session.flush()
    return enemy


async def get_current_enemy(session: AsyncSession, player_id: str) -> Enemy | None:
    player = await session.get(Player, player_id, with_for_update=True)
    if player is None:
        return None
    if player.current_enemy_id is None:
        player.current_enemy_id = (await ensure_enemy(session, player.highest_unlocked_stage)).id
        await session.flush()
    return await session.get(Enemy, player.current_enemy_id)


async def get_enemy_progress(session: AsyncSession, player_id: str) -> tuple[int, Enemy, list[Enemy]] | None:
    player = await session.get(Player, player_id, with_for_update=True)
    if player is None:
        return None
    current = await get_current_enemy(session, player_id)
    if current is None:
        return None
    enemies = [await ensure_enemy(session, stage) for stage in range(1, player.highest_unlocked_stage + 1)]
    return player.highest_unlocked_stage, current, enemies


async def create_pve_battle(
    session: AsyncSession,
    player_id: str,
    *,
    enemy_stage: int | None = None,
    seed: int | None = None,
) -> Battle | None:
    player_result = await session.execute(
        select(Player)
        .options(
            selectinload(Player.cats),
            selectinload(Player.currencies),
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
    if enemy_stage is None:
        enemy = await get_current_enemy(session, player_id)
    elif enemy_stage <= player.highest_unlocked_stage:
        enemy = await ensure_enemy(session, enemy_stage)
        player.current_enemy_id = enemy.id
    else:
        return None
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
        enemy_stage=enemy.stage,
        seed=battle_seed,
        status="completed",
        result=result,
        player_snapshot=player_snapshot,
        enemy_snapshot=enemy_snapshot,
        turn_count=sum(event["event_type"] == "attack" for event in events),
        events=[BattleEvent(**event) for event in events],
    )
    session.add(battle)
    await session.flush()
    if result == "player":
        if enemy.stage == player.highest_unlocked_stage:
            player.highest_unlocked_stage += 1
            player.current_enemy_id = (await ensure_enemy(session, player.highest_unlocked_stage)).id
        await create_reward(session, battle, player, enemy.stage, battle_seed)
    await session.refresh(battle, attribute_names=["events", "reward"])
    return battle


async def create_reward(
    session: AsyncSession,
    battle: Battle,
    player: Player,
    stage: int,
    seed: int,
) -> Reward:
    existing_result = await session.execute(select(Reward).where(Reward.battle_id == battle.id))
    existing = existing_result.scalar_one_or_none()
    if existing is not None:
        return existing

    currency_amount = stage * COINS_PER_STAGE
    currency = next((item for item in player.currencies if item.currency_type == "coins"), None)
    if currency is None:
        currency = Currency(player_id=player.id, currency_type="coins", balance=0)
        session.add(currency)
        await session.flush()
    currency.balance += currency_amount

    drop = random.Random(seed ^ stage).random() < min(0.15 + (stage // 5) * 0.05, 0.5)
    item_instance_id = None
    if drop:
        definitions_result = await session.execute(select(ItemDefinition).order_by(ItemDefinition.rarity, ItemDefinition.id))
        definitions = list(definitions_result.scalars().all())
        if definitions:
            rare_chance = min(0.1 + (stage // 5) * 0.1, 0.6)
            rare = random.Random(seed ^ (stage * 17)).random() < rare_chance
            eligible = [item for item in definitions if item.rarity == ("rare" if rare else "common")]
            if not eligible:
                eligible = definitions
            definition = eligible[random.Random(seed ^ (stage * 31)).randrange(len(eligible))]
            item = ItemInstance(owner_id=player.id, item_definition_id=definition.id, instance_number=1)
            session.add(item)
            await session.flush()
            item_instance_id = item.id

    reward = Reward(
        battle_id=battle.id,
        player_id=player.id,
        currency_amount=currency_amount,
        item_instance_id=item_instance_id,
    )
    session.add(reward)
    await session.flush()
    return reward


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
        .options(
            selectinload(Battle.events),
            selectinload(Battle.reward).selectinload(Reward.item_instance).selectinload(ItemInstance.definition),
        )
        .where(Battle.id == battle_id)
    )
    return result.scalar_one_or_none()


async def get_player_battles(session: AsyncSession, player_id: str) -> list[Battle]:
    result = await session.execute(
        select(Battle)
        .options(selectinload(Battle.events), selectinload(Battle.reward))
        .where(Battle.player_id == player_id)
        .order_by(Battle.created_at.desc())
    )
    return list(result.scalars().all())


async def get_player_rewards(session: AsyncSession, player_id: str) -> list[Reward]:
    result = await session.execute(
        select(Reward)
        .options(selectinload(Reward.item_instance).selectinload(ItemInstance.definition))
        .where(Reward.player_id == player_id)
        .order_by(Reward.created_at.desc())
    )
    return list(result.scalars().all())
