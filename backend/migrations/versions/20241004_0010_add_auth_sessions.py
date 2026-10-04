"""Add password hashes and player sessions.

Revision ID: 20241004_0010
Revises: 20241004_0009
"""

from alembic import op
import sqlalchemy as sa


revision = "20241004_0010"
down_revision = "20241004_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("players", sa.Column("password_hash", sa.String(length=256), nullable=True))
    op.create_table(
        "player_sessions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("player_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_player_sessions_player_id", "player_sessions", ["player_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_player_sessions_player_id", table_name="player_sessions")
    op.drop_table("player_sessions")
    op.drop_column("players", "password_hash")
