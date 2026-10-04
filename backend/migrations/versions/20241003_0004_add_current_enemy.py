"""Persist each player's current PvE enemy.

Revision ID: 20241003_0004
Revises: 20241003_0003
"""

from alembic import op
import sqlalchemy as sa

revision = "20241003_0004"
down_revision = "20241003_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("players") as batch:
        batch.add_column(sa.Column("current_enemy_id", sa.String(length=64), nullable=True))
        batch.create_foreign_key(
            "fk_players_current_enemy_id_enemies",
            "enemies",
            ["current_enemy_id"],
            ["id"],
        )
        batch.create_index(op.f("ix_players_current_enemy_id"), ["current_enemy_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("players") as batch:
        batch.drop_index(op.f("ix_players_current_enemy_id"))
        batch.drop_constraint("fk_players_current_enemy_id_enemies", type_="foreignkey")
        batch.drop_column("current_enemy_id")
