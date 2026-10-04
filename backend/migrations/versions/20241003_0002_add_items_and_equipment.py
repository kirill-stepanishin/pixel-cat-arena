"""Add item definitions, item instances, and cat equipment.

Revision ID: 20241003_0002
Revises: 20241003_0001
Create Date: 2026-10-03 17:30:05.828-07:00

"""

from alembic import op
import sqlalchemy as sa

revision = "20241003_0002"
down_revision = "20241003_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "item_definitions",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("slot", sa.String(length=20), nullable=False),
        sa.Column("rarity", sa.String(length=20), nullable=False),
        sa.Column("visual_key", sa.String(length=80), nullable=False),
        sa.Column("modifiers", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "item_instances",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("item_definition_id", sa.String(length=64), nullable=False),
        sa.Column("instance_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("equipped_cat_id", sa.String(length=36), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["equipped_cat_id"], ["cats.id"]),
        sa.ForeignKeyConstraint(["item_definition_id"], ["item_definitions.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["players.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "owner_id",
            "item_definition_id",
            "instance_number",
        ),
    )
    op.create_index(op.f("ix_item_instances_owner_id"), "item_instances", ["owner_id"], unique=False)
    op.create_index(
        op.f("ix_item_instances_item_definition_id"),
        "item_instances",
        ["item_definition_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_item_instances_equipped_cat_id"),
        "item_instances",
        ["equipped_cat_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_item_instances_equipped_cat_id"), table_name="item_instances")
    op.drop_index(op.f("ix_item_instances_item_definition_id"), table_name="item_instances")
    op.drop_index(op.f("ix_item_instances_owner_id"), table_name="item_instances")
    op.drop_table("item_instances")
    op.drop_table("item_definitions")
