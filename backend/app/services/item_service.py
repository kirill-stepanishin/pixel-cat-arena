from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.item import ItemDefinition, ItemInstance
from app.models.player import Cat

ITEM_DEFINITIONS = (
    {
        "id": "woven-cap",
        "name": "Woven Cap",
        "slot": "head",
        "rarity": "common",
        "visual_key": "woven-cap",
        "modifiers": {"speed": 1},
    },
    {
        "id": "copper-vest",
        "name": "Copper Vest",
        "slot": "body",
        "rarity": "common",
        "visual_key": "copper-vest",
        "modifiers": {"defense": 2},
    },
    {
        "id": "pixel-sword",
        "name": "Pixel Sword",
        "slot": "weapon",
        "rarity": "common",
        "visual_key": "pixel-sword",
        "modifiers": {"attack": 3},
    },
    {
        "id": "lucky-charm",
        "name": "Lucky Charm",
        "slot": "accessory",
        "rarity": "rare",
        "visual_key": "lucky-charm",
        "modifiers": {"attack": 1, "speed": 1},
    },
)


async def ensure_item_definitions(session: AsyncSession) -> list[ItemDefinition]:
    result = await session.execute(select(ItemDefinition))
    definitions = {definition.id: definition for definition in result.scalars().all()}
    missing = [
        ItemDefinition(**definition)
        for definition in ITEM_DEFINITIONS
        if definition["id"] not in definitions
    ]
    if missing:
        session.add_all(missing)
        await session.flush()
        definitions.update({definition.id: definition for definition in missing})
    return [definitions[item["id"]] for item in ITEM_DEFINITIONS]


async def get_player_items(session: AsyncSession, player_id: str) -> list[ItemInstance]:
    result = await session.execute(
        select(ItemInstance)
        .options(selectinload(ItemInstance.definition))
        .where(ItemInstance.owner_id == player_id)
        .order_by(ItemInstance.created_at, ItemInstance.id)
    )
    return list(result.scalars().all())


async def equip_item(
    session: AsyncSession,
    player_id: str,
    cat_id: str,
    item_id: str,
) -> ItemInstance | None:
    cat_result = await session.execute(
        select(Cat).where(Cat.id == cat_id, Cat.player_id == player_id).with_for_update()
    )
    cat = cat_result.scalar_one_or_none()
    if cat is None:
        return None

    item_result = await session.execute(
        select(ItemInstance)
        .options(selectinload(ItemInstance.definition))
        .where(ItemInstance.id == item_id, ItemInstance.owner_id == player_id)
        .with_for_update()
    )
    item = item_result.scalar_one_or_none()
    if item is None:
        return None

    equipped_result = await session.execute(
        select(ItemInstance)
        .join(ItemInstance.definition)
        .where(
            ItemInstance.owner_id == player_id,
            ItemInstance.equipped_cat_id == cat_id,
            ItemDefinition.slot == item.definition.slot,
            ItemInstance.id != item.id,
        )
        .with_for_update()
    )
    currently_equipped = equipped_result.scalars().all()
    for equipped_item in currently_equipped:
        equipped_item.equipped_cat_id = None
    item.equipped_cat_id = cat_id
    await session.flush()
    return item


async def unequip_item(
    session: AsyncSession,
    player_id: str,
    cat_id: str,
    item_id: str,
) -> ItemInstance | None:
    result = await session.execute(
        select(ItemInstance)
        .options(selectinload(ItemInstance.definition))
        .where(
            ItemInstance.id == item_id,
            ItemInstance.owner_id == player_id,
            ItemInstance.equipped_cat_id == cat_id,
        )
        .with_for_update()
    )
    item = result.scalar_one_or_none()
    if item is None:
        return None
    item.equipped_cat_id = None
    await session.flush()
    return item
