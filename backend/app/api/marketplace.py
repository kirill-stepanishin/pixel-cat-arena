from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_player
from app.db import get_session
from app.models.player import Player
from app.schemas.item import ItemRarity, ItemSlot
from app.schemas.marketplace import ListingCreate, ListingRead
from app.services.marketplace_service import (
    MarketplaceError,
    browse_listings,
    cancel_listing,
    create_listing,
    purchase_listing,
)

router = APIRouter(prefix="/marketplace", tags=["marketplace"])


def _raise(error: MarketplaceError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.detail)


@router.post("/listings", response_model=ListingRead, status_code=status.HTTP_201_CREATED)
async def create_marketplace_listing(
    payload: ListingCreate,
    current_player: Annotated[Player, Depends(get_current_player)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ListingRead:
    try:
        listing = await create_listing(session, current_player.id, payload.item_id, payload.price)
    except MarketplaceError as error:
        raise _raise(error) from error
    await session.commit()
    return ListingRead.from_model(listing)


@router.get("/listings", response_model=list[ListingRead])
async def list_marketplace_listings(
    current_player: Annotated[Player, Depends(get_current_player)],
    session: Annotated[AsyncSession, Depends(get_session)],
    slot: ItemSlot | None = None,
    rarity: ItemRarity | None = None,
    scope: Annotated[str, Query(pattern="^(others|mine|all)$")] = "others",
) -> list[ListingRead]:
    listings = await browse_listings(
        session,
        slot=slot,
        rarity=rarity,
        seller_id=current_player.id if scope == "mine" else None,
        exclude_seller_id=current_player.id if scope == "others" else None,
    )
    return [ListingRead.from_model(listing) for listing in listings]


@router.post("/listings/{listing_id}/cancel", response_model=ListingRead)
async def cancel_marketplace_listing(
    listing_id: str,
    current_player: Annotated[Player, Depends(get_current_player)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ListingRead:
    try:
        listing = await cancel_listing(session, current_player.id, listing_id)
    except MarketplaceError as error:
        raise _raise(error) from error
    await session.commit()
    return ListingRead.from_model(listing)


@router.post("/listings/{listing_id}/purchase", response_model=ListingRead)
async def purchase_marketplace_listing(
    listing_id: str,
    current_player: Annotated[Player, Depends(get_current_player)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ListingRead:
    try:
        listing = await purchase_listing(session, current_player.id, listing_id)
    except MarketplaceError as error:
        await session.rollback()
        raise _raise(error) from error
    await session.commit()
    return ListingRead.from_model(listing)
