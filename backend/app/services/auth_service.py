from __future__ import annotations

import base64
import hashlib
import hmac
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.player import Player
from app.models.session import PlayerSession
from app.services.player_service import create_player

_SALT_BYTES = 16


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SALT_BYTES)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return "scrypt$" + base64.urlsafe_b64encode(salt).decode() + "$" + base64.urlsafe_b64encode(digest).decode()


def verify_password(password: str, encoded: str | None) -> bool:
    if not encoded or not encoded.startswith("scrypt$"):
        return False
    _, salt_value, digest_value = encoded.split("$", 2)
    salt = base64.urlsafe_b64decode(salt_value.encode())
    expected = base64.urlsafe_b64decode(digest_value.encode())
    actual = hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1)
    return hmac.compare_digest(actual, expected)


async def register_player(session: AsyncSession, username: str, password: str) -> Player | None:
    existing = await session.scalar(select(Player).where(Player.username == username))
    if existing is not None:
        return None
    player = await create_player(session, username=username, password_hash=hash_password(password))
    return player


async def authenticate_player(
    session: AsyncSession, username: str, password: str
) -> Player | None:
    player = await session.scalar(
        select(Player)
        .options(
            selectinload(Player.cats),
            selectinload(Player.currencies),
            selectinload(Player.items),
        )
        .where(Player.username == username)
    )
    if player is None or not verify_password(password, player.password_hash):
        return None
    return player


async def create_session(session: AsyncSession, player_id: str) -> str:
    token = PlayerSession.new_id()
    session.add(PlayerSession(id=token, player_id=player_id))
    await session.flush()
    return token


async def get_player_by_session(session: AsyncSession, token: str | None) -> Player | None:
    if not token:
        return None
    result = await session.execute(
        select(Player)
        .join(PlayerSession, PlayerSession.player_id == Player.id)
        .options(
            selectinload(Player.cats),
            selectinload(Player.currencies),
            selectinload(Player.items),
        )
        .where(PlayerSession.id == token)
    )
    return result.scalar_one_or_none()


async def delete_session(session: AsyncSession, token: str | None) -> None:
    if token:
        stored = await session.get(PlayerSession, token)
        if stored is not None:
            await session.delete(stored)
