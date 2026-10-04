"""Add enemies, battles, and battle events.

Revision ID: 20241003_0003
Revises: 20241003_0002
"""

from alembic import op
import sqlalchemy as sa

revision = "20241003_0003"
down_revision = "20241003_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "enemies",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("visual_key", sa.String(length=80), nullable=False),
        sa.Column("attack", sa.Integer(), nullable=False),
        sa.Column("defense", sa.Integer(), nullable=False),
        sa.Column("speed", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "battles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("player_id", sa.String(length=36), nullable=False),
        sa.Column("enemy_id", sa.String(length=64), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("result", sa.String(length=20), nullable=False),
        sa.Column("player_snapshot", sa.JSON(), nullable=False),
        sa.Column("enemy_snapshot", sa.JSON(), nullable=False),
        sa.Column("turn_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["enemy_id"], ["enemies.id"]),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_battles_player_id"), "battles", ["player_id"], unique=False)
    op.create_index(op.f("ix_battles_enemy_id"), "battles", ["enemy_id"], unique=False)
    op.create_table(
        "battle_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("battle_id", sa.String(length=36), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("turn_number", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=20), nullable=False),
        sa.Column("attacker", sa.String(length=20), nullable=True),
        sa.Column("damage", sa.Integer(), nullable=False),
        sa.Column("player_hp", sa.Integer(), nullable=False),
        sa.Column("enemy_hp", sa.Integer(), nullable=False),
        sa.Column("elapsed_time", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["battle_id"], ["battles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_battle_events_battle_id"), "battle_events", ["battle_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_battle_events_battle_id"), table_name="battle_events")
    op.drop_table("battle_events")
    op.drop_index(op.f("ix_battles_enemy_id"), table_name="battles")
    op.drop_index(op.f("ix_battles_player_id"), table_name="battles")
    op.drop_table("battles")
    op.drop_table("enemies")
