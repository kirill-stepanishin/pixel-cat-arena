"""Add deterministic PvP match results.

Revision ID: 20241004_0009
Revises: 20241004_0008
"""

from alembic import op
import sqlalchemy as sa


revision = "20241004_0009"
down_revision = "20241004_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pvp_matches",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("challenge_id", sa.String(length=36), nullable=False),
        sa.Column("challenger_id", sa.String(length=36), nullable=False),
        sa.Column("challenged_id", sa.String(length=36), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="completed"),
        sa.Column("result", sa.String(length=20), nullable=False),
        sa.Column("challenger_snapshot", sa.JSON(), nullable=False),
        sa.Column("challenged_snapshot", sa.JSON(), nullable=False),
        sa.Column("events", sa.JSON(), nullable=False),
        sa.Column("turn_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["challenge_id"], ["pvp_challenges.id"]),
        sa.ForeignKeyConstraint(["challenger_id"], ["players.id"]),
        sa.ForeignKeyConstraint(["challenged_id"], ["players.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("challenge_id"),
    )
    for column in ("challenge_id", "challenger_id", "challenged_id"):
        op.create_index(f"ix_pvp_matches_{column}", "pvp_matches", [column], unique=False)


def downgrade() -> None:
    for column in ("challenged_id", "challenger_id", "challenge_id"):
        op.drop_index(f"ix_pvp_matches_{column}", table_name="pvp_matches")
    op.drop_table("pvp_matches")
