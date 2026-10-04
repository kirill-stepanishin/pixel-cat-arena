from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_player
from app.db import get_session
from app.models.player import Player
from app.schemas.auth import AuthResponse, Credentials
from app.services.auth_service import (
    authenticate_player,
    create_session,
    delete_session,
    register_player,
)

router = APIRouter(prefix="/auth", tags=["auth"])
SESSION_COOKIE = "session_token"


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 24 * 30,
    )


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    payload: Credentials,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AuthResponse:
    player = await register_player(session, payload.username, payload.password)
    if player is None:
        raise HTTPException(status_code=409, detail="username already exists")
    token = await create_session(session, player.id)
    await session.commit()
    set_session_cookie(response, token)
    return AuthResponse.model_validate(player)


@router.post("/login", response_model=AuthResponse)
async def login(
    payload: Credentials,
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> AuthResponse:
    player = await authenticate_player(session, payload.username, payload.password)
    if player is None:
        raise HTTPException(status_code=401, detail="invalid username or password")
    token = await create_session(session, player.id)
    await session.commit()
    set_session_cookie(response, token)
    return AuthResponse.model_validate(player)


@router.get("/me", response_model=AuthResponse)
async def me(player: Annotated[Player, Depends(get_current_player)]) -> AuthResponse:
    return AuthResponse.model_validate(player)


@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    session_token: Annotated[str | None, Cookie()] = None,
) -> None:
    await delete_session(session, session_token)
    await session.commit()
    response.delete_cookie(SESSION_COOKIE)
