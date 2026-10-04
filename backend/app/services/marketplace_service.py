from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.item import ItemDefinition, ItemInstance
from app.models.marketplace import MarketplaceListing
from app.models.player import Currency, Player


class MarketplaceError(Exception):
    def __init__(self, detail: str, status_code: int) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


def _listing_options():
    return (
        selectinload(MarketplaceListing.seller),
        selectinload(MarketplaceListing.item).selectinload(ItemInstance.definition),
    )


async def has_active_listing(session: AsyncSession, item_id: str) -> bool:
    listing_id = await session.scalar(
        select(MarketplaceListing.id).where(
            MarketplaceListing.item_instance_id == item_id,
            MarketplaceListing.status == "active",
        )
    )
    return listing_id is not None


async def _get_coins(session: AsyncSession, player_id: str, *, create: bool) -> Currency | None:
    currency = await session.scalar(
        select(Currency)
        .where(Currency.player_id == player_id, Currency.currency_type == "coins")
        .with_for_update()
    )
    if currency is None and create:
        currency = Currency(player_id=player_id, currency_type="coins", balance=0)
        session.add(currency)
        await session.flush()
    return currency


async def create_listing(
    session: AsyncSession, seller_id: str, item_id: str, price: int
) -> MarketplaceListing:
    item = await session.scalar(
        select(ItemInstance)
        .options(selectinload(ItemInstance.definition))
        .where(ItemInstance.id == item_id, ItemInstance.owner_id == seller_id)
        .with_for_update()
    )
    if item is None:
        raise MarketplaceError("owned item not found", 404)
    if item.equipped_cat_id is not None:
        raise MarketplaceError("unequip the item before listing it", 409)
    if await has_active_listing(session, item.id):
        raise MarketplaceError("item is already listed", 409)

    listing = MarketplaceListing(
        seller_id=seller_id, item_instance_id=item.id, price=price, status="active"
    )
    session.add(listing)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise MarketplaceError("item is already listed", 409) from exc
    return await get_listing(session, listing.id)


async def get_listing(session: AsyncSession, listing_id: str) -> MarketplaceListing:
    listing = await session.scalar(
        select(MarketplaceListing)
        .options(*_listing_options())
        .where(MarketplaceListing.id == listing_id)
        .execution_options(populate_existing=True)
    )
    if listing is None:
        raise MarketplaceError("listing not found", 404)
    return listing


async def browse_listings(
    session: AsyncSession,
    *,
    slot: str | None = None,
    rarity: str | None = None,
    seller_id: str | None = None,
    exclude_seller_id: str | None = None,
) -> list[MarketplaceListing]:
    query = (
        select(MarketplaceListing)
        .options(*_listing_options())
        .join(ItemInstance, MarketplaceListing.item_instance_id == ItemInstance.id)
        .join(ItemDefinition, ItemInstance.item_definition_id == ItemDefinition.id)
        .where(MarketplaceListing.status == "active")
        .order_by(MarketplaceListing.created_at.desc(), MarketplaceListing.id)
    )
    if slot:
        query = query.where(ItemDefinition.slot == slot)
    if rarity:
        query = query.where(ItemDefinition.rarity == rarity)
    if seller_id:
        query = query.where(MarketplaceListing.seller_id == seller_id)
    if exclude_seller_id:
        query = query.where(MarketplaceListing.seller_id != exclude_seller_id)
    result = await session.execute(query)
    return list(result.scalars().all())


async def cancel_listing(
    session: AsyncSession, seller_id: str, listing_id: str
) -> MarketplaceListing:
    listing = await session.scalar(
        select(MarketplaceListing).where(MarketplaceListing.id == listing_id).with_for_update()
    )
    if listing is None:
        raise MarketplaceError("listing not found", 404)
    if listing.seller_id != seller_id:
        raise MarketplaceError("only the seller can cancel a listing", 403)
    if listing.status != "active":
        raise MarketplaceError(f"listing is already {listing.status}", 409)

    listing.status = "cancelled"
    listing.closed_at = datetime.now(UTC)
    await session.flush()
    return await get_listing(session, listing.id)


async def purchase_listing(
    session: AsyncSession, buyer_id: str, listing_id: str
) -> MarketplaceListing:
    listing = await session.scalar(
        select(MarketplaceListing).where(MarketplaceListing.id == listing_id).with_for_update()
    )
    if listing is None:
        raise MarketplaceError("listing not found", 404)
    if listing.status != "active":
        raise MarketplaceError(f"listing is already {listing.status}", 409)
    if listing.seller_id == buyer_id:
        raise MarketplaceError("you cannot buy your own listing", 400)

    item = await session.scalar(
        select(ItemInstance).where(ItemInstance.id == listing.item_instance_id).with_for_update()
    )
    if item is None or item.owner_id != listing.seller_id or item.equipped_cat_id is not None:
        raise MarketplaceError("listed item is no longer available", 409)

    buyer = await session.get(Player, buyer_id)
    if buyer is None:
        raise MarketplaceError("buyer not found", 404)

    # Lock balances in a stable order so concurrent trades cannot deadlock.
    locked: dict[str, Currency] = {}
    for player_id in sorted({buyer_id, listing.seller_id}):
        currency = await _get_coins(session, player_id, create=player_id == listing.seller_id)
        if currency is not None:
            locked[player_id] = currency
    buyer_coins = locked.get(buyer_id)
    if buyer_coins is None or buyer_coins.balance < listing.price:
        raise MarketplaceError("not enough coins", 402)

    next_number = await session.scalar(
        select(func.max(ItemInstance.instance_number)).where(
            ItemInstance.owner_id == buyer_id,
            ItemInstance.item_definition_id == item.item_definition_id,
        )
    )
    buyer_coins.balance -= listing.price
    locked[listing.seller_id].balance += listing.price
    item.owner_id = buyer_id
    item.instance_number = (next_number or 0) + 1
    item.equipped_cat_id = None
    listing.status = "sold"
    listing.buyer_id = buyer_id
    listing.closed_at = datetime.now(UTC)
    await session.flush()
    return await get_listing(session, listing.id)
