from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class BuildSnapshot(Base):
    __tablename__ = "build_snapshots"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    player_id: Mapped[str] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    cat_id: Mapped[str] = mapped_column(ForeignKey("cats.id"), nullable=False, index=True)
    cat_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    equipment_snapshot: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
