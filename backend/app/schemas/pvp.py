from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.schemas.battle import BattleEventRead, CombatantSnapshot


class PvpMatchRead(BaseModel):
    id: str
    challenge_id: str
    challenger_id: str
    challenged_id: str
    seed: int
    status: Literal["completed"]
    result: Literal["challenger", "challenged"]
    challenger_snapshot: CombatantSnapshot
    challenged_snapshot: CombatantSnapshot
    turn_count: int
    created_at: datetime
    events: list[BattleEventRead]

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, match) -> PvpMatchRead:
        return cls(
            id=match.id,
            challenge_id=match.challenge_id,
            challenger_id=match.challenger_id,
            challenged_id=match.challenged_id,
            seed=match.seed,
            status=match.status,
            result=match.result,
            challenger_snapshot=CombatantSnapshot.model_validate(match.challenger_snapshot),
            challenged_snapshot=CombatantSnapshot.model_validate(match.challenged_snapshot),
            turn_count=match.turn_count,
            created_at=match.created_at,
            events=[BattleEventRead.model_validate(event) for event in match.events],
        )
