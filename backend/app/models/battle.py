from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.player import Player


class Enemy(Base):
    __tablename__ = "enemies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    stage: Mapped[int] = mapped_column(Integer, unique=True, index=True, nullable=False, default=1)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    visual_key: Mapped[str] = mapped_column(String(80), nullable=False)
    attack: Mapped[int] = mapped_column(Integer, nullable=False)
    defense: Mapped[int] = mapped_column(Integer, nullable=False)
    speed: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    battles: Mapped[list[Battle]] = relationship(back_populates="enemy")


class Battle(Base):
    __tablename__ = "battles"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    player_id: Mapped[str] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    enemy_id: Mapped[str] = mapped_column(ForeignKey("enemies.id"), nullable=False, index=True)
    enemy_stage: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    player_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    enemy_snapshot: Mapped[dict[str, object]] = mapped_column(JSON, nullable=False)
    turn_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    player: Mapped[Player] = relationship()
    enemy: Mapped[Enemy] = relationship(back_populates="battles")
    events: Mapped[list[BattleEvent]] = relationship(
        back_populates="battle",
        cascade="all, delete-orphan",
        order_by="BattleEvent.sequence",
    )
    reward: Mapped["Reward | None"] = relationship(back_populates="battle", uselist=False)


class BattleEvent(Base):
    __tablename__ = "battle_events"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    battle_id: Mapped[str] = mapped_column(ForeignKey("battles.id"), nullable=False, index=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(20), nullable=False)
    attacker: Mapped[str | None] = mapped_column(String(20), nullable=True)
    damage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    player_hp: Mapped[int] = mapped_column(Integer, nullable=False)
    enemy_hp: Mapped[int] = mapped_column(Integer, nullable=False)
    elapsed_time: Mapped[float] = mapped_column(nullable=False, default=0)

    battle: Mapped[Battle] = relationship(back_populates="events")


class Reward(Base):
    __tablename__ = "rewards"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    battle_id: Mapped[str] = mapped_column(ForeignKey("battles.id"), unique=True, nullable=False, index=True)
    player_id: Mapped[str] = mapped_column(ForeignKey("players.id"), nullable=False, index=True)
    currency_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    item_instance_id: Mapped[str | None] = mapped_column(
        ForeignKey("item_instances.id"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    battle: Mapped[Battle] = relationship(back_populates="reward")
    item_instance: Mapped["ItemInstance | None"] = relationship()
