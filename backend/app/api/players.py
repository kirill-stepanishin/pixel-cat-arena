from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.player import Player
from app.schemas.player import PlayerCreate, PlayerWithDetails
from app.services.player_service import get_or_create_development_player, get_player_with_details

router = APIRouter(prefix="/players", tags=["players"])


@router.post("", response_model=PlayerWithDetails)
async def create_player(
    payload: PlayerCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PlayerWithDetails:
    player = await get_or_create_development_player(session, username=payload.username)
    await session.commit()
    return PlayerWithDetails.model_validate(player)


@router.post("/dev", response_model=PlayerWithDetails, include_in_schema=False)
async def create_dev_player(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PlayerWithDetails:
    player = await get_or_create_development_player(session)
    await session.commit()
    return PlayerWithDetails.model_validate(player)


@router.get("/{player_id}", response_model=PlayerWithDetails)
async def get_player(
    player_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PlayerWithDetails:
    player = await get_player_with_details(session, player_id)
    if player is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="player not found")
    return PlayerWithDetails.model_validate(player)


@router.get("", response_model=list[PlayerWithDetails])
async def get_players(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[PlayerWithDetails]:
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    result = await session.execute(
        select(Player)
        .options(selectinload(Player.cats), selectinload(Player.currencies))
    )
    players = result.scalars().all()
    return [PlayerWithDetails.model_validate(player) for player in players]
