from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ItemSlot = Literal["head", "body", "weapon", "accessory"]
StatKey = Literal["attack", "defense", "speed"]
ItemRarity = Literal["common", "rare", "epic", "legendary"]


class StatModifiers(BaseModel):
    attack: int = Field(default=0, ge=-100, le=100)
    defense: int = Field(default=0, ge=-100, le=100)
    speed: int = Field(default=0, ge=-100, le=100)


class ItemDefinitionRead(BaseModel):
    id: str
    name: str
    slot: ItemSlot
    rarity: ItemRarity
    visual_key: str
    modifiers: StatModifiers
    primary_stat: StatKey
    primary_min: int
    primary_max: int
    bonus_stat_count: int
    bonus_min: int
    bonus_max: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ItemInstanceRead(BaseModel):
    id: str
    owner_id: str
    item_definition_id: str
    equipped_cat_id: str | None
    created_at: datetime
    modifiers: StatModifiers
    definition: ItemDefinitionRead

    model_config = ConfigDict(from_attributes=True)
