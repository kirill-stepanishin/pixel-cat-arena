"""Add item roll rules and instance modifiers.

Revision ID: 20241003_0006
Revises: 20241003_0005
"""

from alembic import op
import sqlalchemy as sa


revision = "20241003_0006"
down_revision = "20241003_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("item_definitions", sa.Column("primary_stat", sa.String(length=20), nullable=False, server_default="attack"))
    op.add_column("item_definitions", sa.Column("primary_min", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("item_definitions", sa.Column("primary_max", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("item_definitions", sa.Column("bonus_stat_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("item_definitions", sa.Column("bonus_min", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("item_definitions", sa.Column("bonus_max", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("item_instances", sa.Column("rolled_modifiers", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("item_instances", "rolled_modifiers")
    op.drop_column("item_definitions", "bonus_max")
    op.drop_column("item_definitions", "bonus_min")
    op.drop_column("item_definitions", "bonus_stat_count")
    op.drop_column("item_definitions", "primary_max")
    op.drop_column("item_definitions", "primary_min")
    op.drop_column("item_definitions", "primary_stat")
