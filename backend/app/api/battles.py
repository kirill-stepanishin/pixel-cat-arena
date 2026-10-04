from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.schemas.battle import BattleRead, EnemyRead, PveBattleCreate
from app.services.battle_service import create_pve_battle, get_battle, get_current_enemy

router = APIRouter(prefix="/battles", tags=["battles"])


@router.post("/pve", response_model=BattleRead)
async def create_pve(
    payload: PveBattleCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BattleRead:
    battle = await create_pve_battle(session, payload.player_id)
    if battle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="player or cat not found",
        )
    await session.commit()
    return BattleRead.model_validate(battle)


@router.get("/pve/current/{player_id}", response_model=EnemyRead)
async def read_current_enemy(
    player_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> EnemyRead:
    enemy = await get_current_enemy(session, player_id)
    if enemy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="player not found")
    await session.commit()
    return EnemyRead.model_validate(enemy)


@router.get("/{battle_id}", response_model=BattleRead)
async def read_battle(
    battle_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> BattleRead:
    battle = await get_battle(session, battle_id)
    if battle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="battle not found")
    return BattleRead.model_validate(battle)
