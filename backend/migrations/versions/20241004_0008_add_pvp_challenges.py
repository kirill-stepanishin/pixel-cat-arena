"""Add pending PvP challenges.

Revision ID: 20241004_0008
Revises: 20241004_0007
"""

from alembic import op
import sqlalchemy as sa


revision = "20241004_0008"
down_revision = "20241004_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pvp_challenges",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("challenger_id", sa.String(length=36), nullable=False),
        sa.Column("challenged_id", sa.String(length=36), nullable=False),
        sa.Column("challenger_build_id", sa.String(length=36), nullable=False),
        sa.Column("challenged_build_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["challenger_id"], ["players.id"]),
        sa.ForeignKeyConstraint(["challenged_id"], ["players.id"]),
        sa.ForeignKeyConstraint(["challenger_build_id"], ["build_snapshots.id"]),
        sa.ForeignKeyConstraint(["challenged_build_id"], ["build_snapshots.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("challenger_id", "challenged_id", "challenger_build_id", "challenged_build_id", "status"):
        op.create_index(f"ix_pvp_challenges_{column}", "pvp_challenges", [column], unique=False)


def downgrade() -> None:
    for column in ("status", "challenged_build_id", "challenger_build_id", "challenged_id", "challenger_id"):
        op.drop_index(f"ix_pvp_challenges_{column}", table_name="pvp_challenges")
    op.drop_table("pvp_challenges")
