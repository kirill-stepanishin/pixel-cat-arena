from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from app.schemas.build import BuildSnapshotRead


class PvpChallengeCreate(BaseModel):
    challenger_id: str
    challenged_player_id: str | None = None
    challenged_username: str | None = None

    @model_validator(mode="after")
    def require_one_target(self) -> PvpChallengeCreate:
        if bool(self.challenged_player_id) == bool(self.challenged_username):
            raise ValueError("provide exactly one challenged_player_id or challenged_username")
        return self


class PvpChallengeRead(BaseModel):
    id: str
    challenger_id: str
    challenged_id: str
    challenger_build: BuildSnapshotRead
    challenged_build: BuildSnapshotRead
    status: Literal["pending", "completed"]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_model(cls, challenge) -> PvpChallengeRead:
        return cls(
            id=challenge.id,
            challenger_id=challenge.challenger_id,
            challenged_id=challenge.challenged_id,
            challenger_build=BuildSnapshotRead.from_model(challenge.challenger_build),
            challenged_build=BuildSnapshotRead.from_model(challenge.challenged_build),
            status=challenge.status,
            created_at=challenge.created_at,
        )
