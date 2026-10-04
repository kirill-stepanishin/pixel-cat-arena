from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.build import BuildSnapshot
from app.models.item import ItemInstance
from app.models.player import Player

MAX_HP = 100


def _cat_snapshot(cat, equipped_items: list[ItemInstance]) -> dict[str, object]:
    modifiers = {
        "attack": sum(item.modifiers.get("attack", 0) for item in equipped_items),
        "defense": sum(item.modifiers.get("defense", 0) for item in equipped_items),
        "speed": sum(item.modifiers.get("speed", 0) for item in equipped_items),
    }
    return {
        "name": cat.name,
        "attack": cat.attack + modifiers["attack"],
        "defense": cat.defense + modifiers["defense"],
        "speed": max(1, cat.speed + modifiers["speed"]),
        "max_hp": MAX_HP,
        "visual_key": "mochi",
    }


def _equipment_snapshot(equipped_items: list[ItemInstance]) -> list[dict[str, object]]:
    return [
        {
            "instance_id": item.id,
            "definition_id": item.definition.id,
            "name": item.definition.name,
            "slot": item.definition.slot,
            "rarity": item.definition.rarity,
            "visual_key": item.definition.visual_key,
            "modifiers": item.modifiers,
        }
        for item in equipped_items
    ]


async def _get_player_for_build(session: AsyncSession, player_id: str) -> Player | None:
    result = await session.execute(
        select(Player)
        .options(
            selectinload(Player.cats),
            selectinload(Player.items).selectinload(ItemInstance.definition),
        )
        .where(Player.id == player_id)
        .with_for_update()
    )
    return result.scalar_one_or_none()


async def publish_build(session: AsyncSession, player_id: str) -> BuildSnapshot | None:
    player = await _get_player_for_build(session, player_id)
    if player is None or not player.cats:
        return None

    cat = player.cats[0]
    equipped_items = [item for item in player.items if item.equipped_cat_id == cat.id]
    current_result = await session.execute(
        select(BuildSnapshot)
        .where(
            BuildSnapshot.player_id == player_id,
            BuildSnapshot.is_current.is_(True),
        )
        .with_for_update()
    )
    for current in current_result.scalars():
        current.is_current = False

    latest_version = await session.scalar(
        select(BuildSnapshot.version)
        .where(BuildSnapshot.player_id == player_id)
        .order_by(BuildSnapshot.version.desc())
        .limit(1)
    )
    snapshot = BuildSnapshot(
        player_id=player_id,
        cat_id=cat.id,
        cat_snapshot=_cat_snapshot(cat, equipped_items),
        equipment_snapshot=_equipment_snapshot(equipped_items),
        is_current=True,
        version=(latest_version or 0) + 1,
    )
    session.add(snapshot)
    await session.flush()
    return snapshot


async def get_published_build(session: AsyncSession, player_id: str) -> BuildSnapshot | None:
    result = await session.execute(
        select(BuildSnapshot).where(
            BuildSnapshot.player_id == player_id,
            BuildSnapshot.is_current.is_(True),
        )
    )
    return result.scalar_one_or_none()
