from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PlayerCreate(BaseModel):
    username: str = Field(default="dev-player", min_length=3, max_length=50)


class CurrencyRead(BaseModel):
    id: str
    player_id: str
    currency_type: str
    balance: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CatRead(BaseModel):
    id: str
    player_id: str
    name: str
    attack: int
    defense: int
    speed: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PlayerRead(BaseModel):
    id: str
    username: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PlayerWithDetails(PlayerRead):
    cats: list[CatRead] = []
    currencies: list[CurrencyRead] = []
