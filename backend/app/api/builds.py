from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_player, require_player
from app.db import get_session
from app.models.player import Player
from app.schemas.build import BuildSnapshotRead
from app.services.build_service import get_published_build, publish_build

router = APIRouter(prefix="/builds", tags=["builds"])


@router.post("/{player_id}/publish", response_model=BuildSnapshotRead)
async def publish_player_build(
    player_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_player: Annotated[Player, Depends(get_current_player)],
) -> BuildSnapshotRead:
    require_player(player_id, current_player)
    snapshot = await publish_build(session, player_id)
    if snapshot is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="player or cat not found",
        )
    await session.commit()
    return BuildSnapshotRead.from_model(snapshot)


@router.get("/{player_id}/published", response_model=BuildSnapshotRead)
async def read_published_build(
    player_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_player: Annotated[Player, Depends(get_current_player)],
) -> BuildSnapshotRead:
    require_player(player_id, current_player)
    snapshot = await get_published_build(session, player_id)
    if snapshot is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="published build not found")
    return BuildSnapshotRead.from_model(snapshot)
