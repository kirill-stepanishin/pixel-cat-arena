from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_current_player, require_player
from app.db import get_session
from app.models.item import ItemInstance
from app.models.player import Player
from app.schemas.item import ItemDefinitionRead, ItemInstanceRead
from app.services.item_service import (
    ItemListedError,
    ItemSaleError,
    SolanaExportError,
    claim_item_nft,
    ensure_item_definitions,
    equip_item,
    get_player_items,
    list_claimable_items,
    mint_item_nft,
    sell_item,
    unequip_item,
)

router = APIRouter(prefix="/players", tags=["items"])


@router.get("/{player_id}/items", response_model=list[ItemInstanceRead])
async def get_inventory(
    player_id: str,
    current_player: Annotated[Player, Depends(get_current_player)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ItemInstanceRead]:
    require_player(player_id, current_player)
    return [ItemInstanceRead.model_validate(item) for item in await get_player_items(session, player_id)]


@router.get("/items/definitions", response_model=list[ItemDefinitionRead])
async def get_item_definitions(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ItemDefinitionRead]:
    definitions = await ensure_item_definitions(session)
    await session.commit()
    return [ItemDefinitionRead.model_validate(definition) for definition in definitions]


class SaleResult(BaseModel):
    item_id: str
    item_name: str
    price: int
    balance: int


@router.post("/items/{item_id}/sell", response_model=SaleResult)
async def sell_inventory_item(
    item_id: str,
    current_player: Annotated[Player, Depends(get_current_player)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> SaleResult:
    try:
        item, price, balance = await sell_item(session, current_player.id, item_id)
    except ItemSaleError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    await session.commit()
    return SaleResult(item_id=item_id, item_name=item.definition.name, price=price, balance=balance)


@router.post(
    "/{player_id}/cats/{cat_id}/items/{item_id}/equip",
    response_model=ItemInstanceRead,
)
async def equip_inventory_item(
    player_id: str,
    cat_id: str,
    item_id: str,
    current_player: Annotated[Player, Depends(get_current_player)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ItemInstanceRead:
    require_player(player_id, current_player)
    try:
        item = await equip_item(session, player_id, cat_id, item_id)
    except ItemListedError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="cancel the marketplace listing before equipping this item",
        ) from error
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="owned item or cat not found",
        )
    await session.commit()
    return ItemInstanceRead.model_validate(item)


@router.post(
    "/{player_id}/cats/{cat_id}/items/{item_id}/unequip",
    response_model=ItemInstanceRead,
)
async def unequip_inventory_item(
    player_id: str,
    cat_id: str,
    item_id: str,
    current_player: Annotated[Player, Depends(get_current_player)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ItemInstanceRead:
    require_player(player_id, current_player)
    item = await unequip_item(session, player_id, cat_id, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="equipped item not found")
    await session.commit()
    return ItemInstanceRead.model_validate(item)


class MintNftRequest(BaseModel):
    wallet_address: str


@router.post("/items/{item_id}/mint-nft", response_model=ItemInstanceRead)
async def mint_item_as_nft(
    item_id: str,
    payload: MintNftRequest,
    current_player: Annotated[Player, Depends(get_current_player)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ItemInstanceRead:
    try:
        item = await mint_item_nft(session, current_player.id, item_id, payload.wallet_address)
    except SolanaExportError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    await session.commit()
    return ItemInstanceRead.model_validate(item)


class ClaimNftRequest(BaseModel):
    mint_address: str
    wallet_address: str
    signature: str


@router.post("/items/claim", response_model=ItemInstanceRead)
async def claim_item_from_solana(
    payload: ClaimNftRequest,
    current_player: Annotated[Player, Depends(get_current_player)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ItemInstanceRead:
    try:
        item = await claim_item_nft(
            session,
            current_player.id,
            payload.mint_address,
            payload.wallet_address,
            payload.signature,
        )
    except SolanaExportError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    await session.commit()
    return ItemInstanceRead.model_validate(item)


@router.get("/items/claimable", response_model=list[ItemInstanceRead])
async def claimable_items(
    wallet_address: str,
    current_player: Annotated[Player, Depends(get_current_player)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ItemInstanceRead]:
    # Read-only lookup — no signature needed yet, just to browse what a wallet holds.
    items = await list_claimable_items(session, wallet_address, current_player.id)
    return [ItemInstanceRead.model_validate(item) for item in items]


@router.get("/items/{item_id}/metadata.json", include_in_schema=False)
async def item_nft_metadata(
    item_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    # Public (no auth) — wallets, explorers, and marketplaces must be able to fetch
    # this without a session cookie.
    item = (
        await session.execute(
            select(ItemInstance)
            .options(selectinload(ItemInstance.definition))
            .where(ItemInstance.id == item_id)
        )
    ).scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="item not found")

    modifiers = item.modifiers
    return {
        "name": item.definition.name,
        "symbol": "PCA",
        "description": "A Pixel Cat Arena legendary item, exported to Solana.",
        "image": f"https://placeholder.pixelcatarena.local/items/{item.definition.visual_key}.png",
        "attributes": [
            {"trait_type": "rarity", "value": item.definition.rarity},
            {"trait_type": "slot", "value": item.definition.slot},
            {"trait_type": "attack", "value": modifiers.get("attack", 0)},
            {"trait_type": "defense", "value": modifiers.get("defense", 0)},
            {"trait_type": "speed", "value": modifiers.get("speed", 0)},
        ],
    }
