import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.player import Cat, Player


class ItemDefinition(Base):
    __tablename__ = "item_definitions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    slot: Mapped[str] = mapped_column(String(20), nullable=False)
    rarity: Mapped[str] = mapped_column(String(20), nullable=False)
    visual_key: Mapped[str] = mapped_column(String(80), nullable=False)
    modifiers: Mapped[dict[str, int]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    instances: Mapped[list["ItemInstance"]] = relationship(back_populates="definition")


class ItemInstance(Base):
    __tablename__ = "item_instances"
    __table_args__ = (
        UniqueConstraint("owner_id", "item_definition_id", "instance_number"),
    )

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    owner_id: Mapped[str] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    item_definition_id: Mapped[str] = mapped_column(
        ForeignKey("item_definitions.id"),
        nullable=False,
        index=True,
    )
    instance_number: Mapped[int] = mapped_column(nullable=False, default=1)
    equipped_cat_id: Mapped[str | None] = mapped_column(
        ForeignKey("cats.id"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    owner: Mapped["Player"] = relationship(back_populates="items")
    definition: Mapped[ItemDefinition] = relationship(back_populates="instances")
    equipped_cat: Mapped["Cat | None"] = relationship(back_populates="equipped_items")
