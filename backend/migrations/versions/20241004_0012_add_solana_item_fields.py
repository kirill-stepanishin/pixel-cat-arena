"""Add Solana NFT export fields to item_instances.

Revision ID: 20241004_0012
Revises: 20241004_0011
"""

from alembic import op
import sqlalchemy as sa


revision = "20241004_0012"
down_revision = "20241004_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "item_instances", sa.Column("solana_mint_address", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "item_instances", sa.Column("solana_owner_wallet", sa.String(length=64), nullable=True)
    )
    op.create_index(
        "uq_item_instances_solana_mint_address",
        "item_instances",
        ["solana_mint_address"],
        unique=True,
        sqlite_where=sa.text("solana_mint_address IS NOT NULL"),
        postgresql_where=sa.text("solana_mint_address IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_item_instances_solana_mint_address", table_name="item_instances")
    op.drop_column("item_instances", "solana_owner_wallet")
    op.drop_column("item_instances", "solana_mint_address")
