"""Create players, cats, and currencies tables.

Revision ID: 20241003_0001
Revises: 
Create Date: 2026-10-03 17:18:54.667-07:00

"""

from alembic import op
import sqlalchemy as sa

revision = "20241003_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "players",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username", name="uq_players_username"),
    )
    op.create_index(op.f("ix_players_id"), "players", ["id"], unique=False)
    op.create_index(op.f("ix_players_username"), "players", ["username"], unique=False)

    op.create_table(
        "cats",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("player_id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False, server_default="Mochi"),
        sa.Column("attack", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("defense", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("speed", sa.Integer(), nullable=False, server_default="6"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cats_player_id"), "cats", ["player_id"], unique=False)

    op.create_table(
        "currencies",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("player_id", sa.String(length=36), nullable=False),
        sa.Column("currency_type", sa.String(length=32), nullable=False, server_default="coins"),
        sa.Column("balance", sa.Integer(), nullable=False, server_default="100"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("player_id", "currency_type", name="uq_currency_player_type"),
    )
    op.create_index(op.f("ix_currencies_player_id"), "currencies", ["player_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_currencies_player_id"), table_name="currencies")
    op.drop_table("currencies")
    op.drop_index(op.f("ix_cats_player_id"), table_name="cats")
    op.drop_table("cats")
    op.drop_index(op.f("ix_players_username"), table_name="players")
    op.drop_index(op.f("ix_players_id"), table_name="players")
    op.drop_table("players")
