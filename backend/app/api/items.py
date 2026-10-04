from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.item import ItemDefinitionRead, ItemInstanceRead
from app.services.item_service import (
    ensure_item_definitions,
    equip_item,
    get_player_items,
    unequip_item,
)

router = APIRouter(prefix="/players", tags=["items"])


@router.get("/{player_id}/items", response_model=list[ItemInstanceRead])
async def get_inventory(
    player_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ItemInstanceRead]:
    return [ItemInstanceRead.model_validate(item) for item in await get_player_items(session, player_id)]


@router.get("/items/definitions", response_model=list[ItemDefinitionRead])
async def get_item_definitions(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ItemDefinitionRead]:
    definitions = await ensure_item_definitions(session)
    await session.commit()
    return [ItemDefinitionRead.model_validate(definition) for definition in definitions]


@router.post(
    "/{player_id}/cats/{cat_id}/items/{item_id}/equip",
    response_model=ItemInstanceRead,
)
async def equip_inventory_item(
    player_id: str,
    cat_id: str,
    item_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ItemInstanceRead:
    item = await equip_item(session, player_id, cat_id, item_id)
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
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ItemInstanceRead:
    item = await unequip_item(session, player_id, cat_id, item_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="equipped item not found")
    await session.commit()
    return ItemInstanceRead.model_validate(item)
