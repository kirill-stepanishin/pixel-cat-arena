from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.challenge import PvpChallenge


class PvpMatch(Base):
    __tablename__ = "pvp_matches"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    challenge_id: Mapped[str] = mapped_column(
        ForeignKey("pvp_challenges.id"),
        unique=True,
        nullable=False,
        index=True,
    )
    challenger_id: Mapped[str] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    challenged_id: Mapped[str] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    challenger_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    challenged_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    events: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)
    turn_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    challenge: Mapped[PvpChallenge] = relationship(back_populates="match")
