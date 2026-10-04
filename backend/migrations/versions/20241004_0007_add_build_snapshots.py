"""Add immutable published build snapshots.

Revision ID: 20241004_0007
Revises: 20241003_0006
"""

from alembic import op
import sqlalchemy as sa


revision = "20241004_0007"
down_revision = "20241003_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "build_snapshots",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("player_id", sa.String(length=36), nullable=False),
        sa.Column("cat_id", sa.String(length=36), nullable=False),
        sa.Column("cat_snapshot", sa.JSON(), nullable=False),
        sa.Column("equipment_snapshot", sa.JSON(), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["cat_id"], ["cats.id"]),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_build_snapshots_player_id", "build_snapshots", ["player_id"], unique=False)
    op.create_index("ix_build_snapshots_cat_id", "build_snapshots", ["cat_id"], unique=False)
    op.create_index("ix_build_snapshots_is_current", "build_snapshots", ["is_current"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_build_snapshots_is_current", table_name="build_snapshots")
    op.drop_index("ix_build_snapshots_cat_id", table_name="build_snapshots")
    op.drop_index("ix_build_snapshots_player_id", table_name="build_snapshots")
    op.drop_table("build_snapshots")
