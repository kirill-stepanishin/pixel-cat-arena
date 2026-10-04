from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.battle import CombatantSnapshot
from app.schemas.item import StatModifiers


class BuildEquipmentSnapshot(BaseModel):
    instance_id: str
    definition_id: str
    name: str
    slot: str
    rarity: str
    visual_key: str
    modifiers: StatModifiers


class BuildSnapshotRead(BaseModel):
    id: str
    player_id: str
    cat_id: str
    version: int
    cat: CombatantSnapshot
    equipment: list[BuildEquipmentSnapshot]
    is_current: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, snapshot) -> BuildSnapshotRead:
        return cls(
            id=snapshot.id,
            player_id=snapshot.player_id,
            cat_id=snapshot.cat_id,
            version=snapshot.version,
            cat=CombatantSnapshot.model_validate(snapshot.cat_snapshot),
            equipment=[
                BuildEquipmentSnapshot.model_validate(item)
                for item in snapshot.equipment_snapshot
            ],
            is_current=snapshot.is_current,
            created_at=snapshot.created_at,
        )
