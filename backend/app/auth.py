from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.player import Player
from app.services.auth_service import get_player_by_session


async def get_current_player(
    session: Annotated[AsyncSession, Depends(get_session)],
    session_token: Annotated[str | None, Cookie()] = None,
) -> Player:
    player = await get_player_by_session(session, session_token)
    if player is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required")
    return player


def require_player(player_id: str, current_player: Player) -> str:
    if player_id != current_player.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="player access denied")
    return player_id
