from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.item import ItemInstance
from app.models.player import Player


class MarketplaceListing(Base):
    __tablename__ = "marketplace_listings"
    __table_args__ = (
        CheckConstraint("price > 0", name="ck_marketplace_listings_price_positive"),
        Index(
            "uq_marketplace_listings_active_item",
            "item_instance_id",
            unique=True,
            sqlite_where=text("status = 'active'"),
            postgresql_where=text("status = 'active'"),
        ),
        Index("ix_marketplace_listings_status_created", "status", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    seller_id: Mapped[str] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    buyer_id: Mapped[str | None] = mapped_column(ForeignKey("players.id"), nullable=True, index=True)
    item_instance_id: Mapped[str] = mapped_column(
        ForeignKey("item_instances.id"), nullable=False, index=True
    )
    price: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    seller: Mapped[Player] = relationship(foreign_keys=[seller_id])
    buyer: Mapped[Player | None] = relationship(foreign_keys=[buyer_id])
    item: Mapped[ItemInstance] = relationship()
