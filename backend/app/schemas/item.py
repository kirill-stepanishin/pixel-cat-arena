from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.content.items import sell_value

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
    solana_mint_address: str | None = None
    solana_owner_wallet: str | None = None

    model_config = ConfigDict(from_attributes=True)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def sell_price(self) -> int:
        total = self.modifiers.attack + self.modifiers.defense + self.modifiers.speed
        return sell_value(self.definition.rarity, total)
