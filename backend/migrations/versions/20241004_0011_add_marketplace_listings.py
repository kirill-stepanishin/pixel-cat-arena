"""Add marketplace listings.

Revision ID: 20241004_0011
Revises: 20241004_0010
"""

from alembic import op
import sqlalchemy as sa


revision = "20241004_0011"
down_revision = "20241004_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "marketplace_listings",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("seller_id", sa.String(length=36), nullable=False),
        sa.Column("buyer_id", sa.String(length=36), nullable=True),
        sa.Column("item_instance_id", sa.String(length=36), nullable=False),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("price > 0", name="ck_marketplace_listings_price_positive"),
        sa.ForeignKeyConstraint(["seller_id"], ["players.id"]),
        sa.ForeignKeyConstraint(["buyer_id"], ["players.id"]),
        sa.ForeignKeyConstraint(["item_instance_id"], ["item_instances.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("seller_id", "buyer_id", "item_instance_id"):
        op.create_index(f"ix_marketplace_listings_{column}", "marketplace_listings", [column])
    op.create_index(
        "ix_marketplace_listings_status_created", "marketplace_listings", ["status", "created_at"]
    )
    op.create_index(
        "uq_marketplace_listings_active_item",
        "marketplace_listings",
        ["item_instance_id"],
        unique=True,
        sqlite_where=sa.text("status = 'active'"),
        postgresql_where=sa.text("status = 'active'"),
    )


def downgrade() -> None:
    op.drop_index("uq_marketplace_listings_active_item", table_name="marketplace_listings")
    op.drop_index("ix_marketplace_listings_status_created", table_name="marketplace_listings")
    for column in ("item_instance_id", "buyer_id", "seller_id"):
        op.drop_index(f"ix_marketplace_listings_{column}", table_name="marketplace_listings")
    op.drop_table("marketplace_listings")
