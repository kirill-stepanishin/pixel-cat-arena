import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.battle import Enemy
    from app.models.item import ItemInstance


class Player(Base):
    __tablename__ = "players"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
        index=True,
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    current_enemy_id: Mapped[str | None] = mapped_column(
        ForeignKey("enemies.id"),
        nullable=True,
        index=True,
    )
    highest_unlocked_stage: Mapped[int] = mapped_column(default=1, nullable=False)

    cats: Mapped[list["Cat"]] = relationship(
        back_populates="player",
        cascade="all, delete-orphan",
    )
    currencies: Mapped[list["Currency"]] = relationship(
        back_populates="player",
        cascade="all, delete-orphan",
    )
    items: Mapped[list["ItemInstance"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    current_enemy: Mapped["Enemy | None"] = relationship()


class Cat(Base):
    __tablename__ = "cats"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    player_id: Mapped[str] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, default="Mochi")
    attack: Mapped[int] = mapped_column(default=10, nullable=False)
    defense: Mapped[int] = mapped_column(default=8, nullable=False)
    speed: Mapped[int] = mapped_column(default=6, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    player: Mapped[Player] = relationship(back_populates="cats")
    equipped_items: Mapped[list["ItemInstance"]] = relationship(back_populates="equipped_cat")


class Currency(Base):
    __tablename__ = "currencies"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    player_id: Mapped[str] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    currency_type: Mapped[str] = mapped_column(String(32), nullable=False, default="coins")
    balance: Mapped[int] = mapped_column(default=100, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    player: Mapped[Player] = relationship(back_populates="currencies")
