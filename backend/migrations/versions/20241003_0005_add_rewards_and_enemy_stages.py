"""Add scalable enemy stages and atomic rewards.

Revision ID: 20241003_0005
Revises: 20241003_0004
"""

from alembic import op
import sqlalchemy as sa

revision = "20241003_0005"
down_revision = "20241003_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("players") as batch:
        batch.add_column(sa.Column("highest_unlocked_stage", sa.Integer(), nullable=False, server_default="1"))

    with op.batch_alter_table("enemies") as batch:
        batch.add_column(sa.Column("stage", sa.Integer(), nullable=True))

    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE enemies SET stage = CAST(SUBSTR(id, 7) AS INTEGER) WHERE stage IS NULL")
    )

    with op.batch_alter_table("enemies") as batch:
        batch.alter_column("stage", nullable=False)
        batch.create_index("ix_enemies_stage", ["stage"], unique=True)

    with op.batch_alter_table("battles") as batch:
        batch.add_column(sa.Column("enemy_stage", sa.Integer(), nullable=False, server_default="1"))

    op.create_table(
        "rewards",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("battle_id", sa.String(length=36), nullable=False),
        sa.Column("player_id", sa.String(length=36), nullable=False),
        sa.Column("currency_amount", sa.Integer(), nullable=False),
        sa.Column("item_instance_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["battle_id"], ["battles.id"]),
        sa.ForeignKeyConstraint(["item_instance_id"], ["item_instances.id"]),
        sa.ForeignKeyConstraint(["player_id"], ["players.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("battle_id"),
    )
    op.create_index("ix_rewards_battle_id", "rewards", ["battle_id"], unique=True)
    op.create_index("ix_rewards_player_id", "rewards", ["player_id"], unique=False)
    op.create_index("ix_rewards_item_instance_id", "rewards", ["item_instance_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_rewards_item_instance_id", table_name="rewards")
    op.drop_index("ix_rewards_player_id", table_name="rewards")
    op.drop_index("ix_rewards_battle_id", table_name="rewards")
    op.drop_table("rewards")
    with op.batch_alter_table("battles") as batch:
        batch.drop_column("enemy_stage")
    with op.batch_alter_table("enemies") as batch:
        batch.drop_index("ix_enemies_stage")
        batch.drop_column("stage")
    with op.batch_alter_table("players") as batch:
        batch.drop_column("highest_unlocked_stage")
