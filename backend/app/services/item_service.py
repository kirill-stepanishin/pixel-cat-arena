from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.content.items import ITEM_TEMPLATES
from app.models.item import ItemDefinition, ItemInstance
from app.models.marketplace import MarketplaceListing
from app.models.player import Cat


class ItemListedError(Exception):
    pass


async def ensure_item_definitions(session: AsyncSession) -> list[ItemDefinition]:
    result = await session.execute(select(ItemDefinition))
    definitions = {definition.id: definition for definition in result.scalars().all()}
    missing = [
        ItemDefinition(modifiers={}, **definition)
        for definition in ITEM_TEMPLATES
        if definition["id"] not in definitions
    ]
    for template in ITEM_TEMPLATES:
        definition = definitions.get(template["id"])
        if definition is not None:
            for field in (
                "name", "slot", "rarity", "visual_key", "primary_stat", "primary_min",
                "primary_max", "bonus_stat_count", "bonus_min", "bonus_max",
            ):
                setattr(definition, field, template[field])
    if missing:
        session.add_all(missing)
        await session.flush()
        definitions.update({definition.id: definition for definition in missing})
    return [definitions[item["id"]] for item in ITEM_TEMPLATES]


def starter_item(item_id: str, player_id: str) -> ItemInstance:
    template = next(item for item in ITEM_TEMPLATES if item["id"] == item_id)
    starter_rolls = {
        "bunny-ears-common": {"speed": 1},
        "leather-armor-common": {"defense": 2},
        "claw-gloves-common": {"attack": 3},
        "bell-collar-common": {"speed": 1},
    }
    return ItemInstance(
        owner_id=player_id,
        item_definition_id=template["id"],
        instance_number=1,
        rolled_modifiers=starter_rolls[item_id],
    )


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
    listed = await session.scalar(
        select(MarketplaceListing.id).where(
            MarketplaceListing.item_instance_id == item.id,
            MarketplaceListing.status == "active",
        )
    )
    if listed is not None:
        raise ItemListedError

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
