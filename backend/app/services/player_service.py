from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.content.items import STARTER_ITEM_IDS
from app.models.item import ItemInstance
from app.models.player import Cat, Currency, Player
from app.services.item_service import ensure_item_definitions, starter_item


async def get_or_create_development_player(session: AsyncSession, username: str = "dev-player") -> Player:
    statement = (
        select(Player)
        .options(
            selectinload(Player.cats),
            selectinload(Player.currencies),
            selectinload(Player.items),
        )
        .where(Player.username == username)
    )
    result = await session.execute(statement)
    player = result.scalar_one_or_none()
    if player is not None:
        item_result = await session.execute(
            select(ItemInstance.id).where(ItemInstance.owner_id == player.id).limit(1)
        )
        if item_result.scalar_one_or_none() is None:
            await ensure_item_definitions(session)
            starter_items = [starter_item(item_id, player.id) for item_id in STARTER_ITEM_IDS]
            session.add_all(starter_items)
            await session.flush()
        return player

    player = Player(username=username)
    starter_currency = Currency(player_id=player.id, currency_type="coins", balance=125)
    starter_cat = Cat(player_id=player.id, name="Mochi", attack=12, defense=10, speed=8)
    player.currencies = [starter_currency]
    player.cats = [starter_cat]

    session.add(player)
    await session.flush()
    await ensure_item_definitions(session)
    starter_items = [starter_item(item_id, player.id) for item_id in STARTER_ITEM_IDS]
    session.add_all(starter_items)
    await session.flush()
    await session.refresh(player, attribute_names=["cats", "currencies"])
    return player


async def get_player_with_details(session: AsyncSession, player_id: str) -> Player | None:
    statement = (
        select(Player)
        .options(
            selectinload(Player.cats),
            selectinload(Player.currencies),
            selectinload(Player.items).selectinload(ItemInstance.definition),
        )
        .where(Player.id == player_id)
    )
    result = await session.execute(statement)
    return result.scalar_one_or_none()
