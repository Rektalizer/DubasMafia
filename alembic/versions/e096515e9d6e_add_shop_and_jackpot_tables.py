"""add shop and jackpot tables

Revision ID: e096515e9d6e
Revises: fa14aaaee92f
Create Date: 2026-06-22 20:19:40.239767

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e096515e9d6e'
down_revision: Union[str, Sequence[str], None] = 'fa14aaaee92f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "daily_quest_offers",
        sa.Column("double_active", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "jackpot_contributions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quest_date", sa.Date(), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("quest_date", "telegram_user_id"),
    )
    op.create_index("ix_jackpot_contributions_quest_date", "jackpot_contributions", ["quest_date"])
    op.create_index(
        "ix_jackpot_contributions_telegram_user_id",
        "jackpot_contributions",
        ["telegram_user_id"],
    )
    op.create_table(
        "jackpot_state",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("carryover_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.execute("INSERT INTO jackpot_state (id, carryover_amount) VALUES (1, 0)")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_jackpot_contributions_telegram_user_id", table_name="jackpot_contributions")
    op.drop_index("ix_jackpot_contributions_quest_date", table_name="jackpot_contributions")
    op.drop_table("jackpot_contributions")
    op.drop_table("jackpot_state")
    op.drop_column("daily_quest_offers", "double_active")
