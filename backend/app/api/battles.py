from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_player, require_player
from app.db import get_session
from app.models.player import Player
from app.schemas.battle import BattleRead, EnemyProgressRead, EnemyRead, PveBattleCreate, RewardRead, SelectEnemyStage
from app.services.battle_service import (
    create_pve_battle,
    get_battle,
    get_current_enemy,
    get_enemy_progress,
    select_enemy_stage,
)

router = APIRouter(prefix="/battles", tags=["battles"])


@router.post("/pve", response_model=BattleRead)
async def create_pve(
    payload: PveBattleCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_player: Annotated[Player, Depends(get_current_player)],
) -> BattleRead:
    require_player(payload.player_id, current_player)
    battle = await create_pve_battle(session, payload.player_id, enemy_stage=payload.enemy_stage)
    if battle is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="player or cat not found",
        )
    await session.commit()
    saved_battle = await get_battle(session, battle.id)
    return BattleRead.model_validate(saved_battle or battle)


@router.get("/pve/current/{player_id}", response_model=EnemyRead)
async def read_current_enemy(
    player_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_player: Annotated[Player, Depends(get_current_player)],
) -> EnemyRead:
    require_player(player_id, current_player)
    enemy = await get_current_enemy(session, player_id)
    if enemy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="player not found")
    await session.commit()
    return EnemyRead.model_validate(enemy)


@router.get("/pve/enemies/{player_id}", response_model=EnemyProgressRead)
async def read_enemy_progress(
    player_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_player: Annotated[Player, Depends(get_current_player)],
) -> EnemyProgressRead:
    require_player(player_id, current_player)
    progress = await get_enemy_progress(session, player_id)
    if progress is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="player not found")
    highest_stage, selected_enemy, enemies = progress
    return EnemyProgressRead(
        highest_unlocked_stage=highest_stage,
        selected_stage=selected_enemy.stage,
        enemies=[EnemyRead.model_validate(enemy) for enemy in enemies],
    )


@router.post("/pve/select", response_model=EnemyRead)
async def select_enemy(
    payload: SelectEnemyStage,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_player: Annotated[Player, Depends(get_current_player)],
) -> EnemyRead:
    require_player(payload.player_id, current_player)
    enemy = await select_enemy_stage(session, payload.player_id, payload.stage)
    if enemy is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="stage not unlocked")
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


@router.get("/players/{player_id}/history", response_model=list[BattleRead])
async def read_player_battle_history(
    player_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_player: Annotated[Player, Depends(get_current_player)],
) -> list[BattleRead]:
    require_player(player_id, current_player)
    from app.services.battle_service import get_player_battles

    battles = await get_player_battles(session, player_id)
    return [BattleRead.model_validate(battle) for battle in battles]


@router.get("/players/{player_id}/rewards", response_model=list[RewardRead])
async def read_player_rewards(
    player_id: str,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_player: Annotated[Player, Depends(get_current_player)],
) -> list[RewardRead]:
    require_player(player_id, current_player)
    from app.services.battle_service import get_player_rewards

    rewards = await get_player_rewards(session, player_id)
    return [RewardRead.model_validate(reward) for reward in rewards]
