from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.item import ItemInstanceRead


class PveBattleCreate(BaseModel):
    player_id: str = Field(min_length=1)
    enemy_stage: int | None = Field(default=None, ge=1)


class SelectEnemyStage(BaseModel):
    player_id: str = Field(min_length=1)
    stage: int = Field(ge=1)


class EnemyRead(BaseModel):
    id: str
    stage: int
    name: str
    visual_key: str
    attack: int
    defense: int
    speed: int

    model_config = ConfigDict(from_attributes=True)


class CombatantSnapshot(BaseModel):
    name: str
    attack: int
    defense: int
    speed: int
    max_hp: int = 100
    visual_key: str | None = None


class BattleEventRead(BaseModel):
    sequence: int
    turn_number: int
    event_type: Literal["attack", "victory", "defeat"]
    attacker: Literal["player", "enemy"] | None
    damage: int
    player_hp: int
    enemy_hp: int
    elapsed_time: float

    model_config = ConfigDict(from_attributes=True)


class BattleRead(BaseModel):
    id: str
    player_id: str
    enemy_id: str
    enemy_stage: int
    seed: int
    status: Literal["completed"]
    result: Literal["player", "enemy"]
    player_snapshot: CombatantSnapshot
    enemy_snapshot: CombatantSnapshot
    turn_count: int
    created_at: datetime
    events: list[BattleEventRead]
    reward: "RewardRead | None" = None

    model_config = ConfigDict(from_attributes=True)


class RewardRead(BaseModel):
    id: str
    battle_id: str
    player_id: str
    currency_amount: int
    item_instance_id: str | None
    item_instance: ItemInstanceRead | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EnemyProgressRead(BaseModel):
    highest_unlocked_stage: int
    selected_stage: int
    enemies: list[EnemyRead]


class RewardHistoryRead(RewardRead):
    pass
