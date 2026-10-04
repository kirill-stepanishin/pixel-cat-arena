from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PveBattleCreate(BaseModel):
    player_id: str = Field(min_length=1)


class EnemyRead(BaseModel):
    id: str
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
    event_type: Literal["attack", "draw", "victory", "defeat"]
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
    seed: int
    status: Literal["completed"]
    result: Literal["player", "enemy", "draw"]
    player_snapshot: CombatantSnapshot
    enemy_snapshot: CombatantSnapshot
    turn_count: int
    created_at: datetime
    events: list[BattleEventRead]

    model_config = ConfigDict(from_attributes=True)
