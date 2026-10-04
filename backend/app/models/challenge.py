from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.build import BuildSnapshot
from app.models.pvp import PvpMatch


class PvpChallenge(Base):
    __tablename__ = "pvp_challenges"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    challenger_id: Mapped[str] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    challenged_id: Mapped[str] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    challenger_build_id: Mapped[str] = mapped_column(
        ForeignKey("build_snapshots.id"), nullable=False, index=True
    )
    challenged_build_id: Mapped[str] = mapped_column(
        ForeignKey("build_snapshots.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    challenger_build: Mapped[BuildSnapshot] = relationship(
        foreign_keys=[challenger_build_id],
    )
    challenged_build: Mapped[BuildSnapshot] = relationship(
        foreign_keys=[challenged_build_id],
    )
    match: Mapped[PvpMatch | None] = relationship(back_populates="challenge", uselist=False)
