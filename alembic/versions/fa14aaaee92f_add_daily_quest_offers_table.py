"""add daily quest offers table

Revision ID: fa14aaaee92f
Revises: a8760ce35164
Create Date: 2026-06-22 19:48:31.592167

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa14aaaee92f'
down_revision: Union[str, Sequence[str], None] = 'a8760ce35164'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "daily_quest_offers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("player_telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("quest_date", sa.Date(), nullable=False),
        sa.Column("options_json", sa.JSON(), nullable=False),
        sa.Column("selected_difficulty", sa.String(length=16), nullable=True),
        sa.Column("selected_quest_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="offered"),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("player_telegram_user_id", "quest_date"),
    )
    op.create_index(
        "ix_daily_quest_offers_player_telegram_user_id",
        "daily_quest_offers",
        ["player_telegram_user_id"],
    )
    op.create_index("ix_daily_quest_offers_quest_date", "daily_quest_offers", ["quest_date"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_daily_quest_offers_quest_date", table_name="daily_quest_offers")
    op.drop_index(
        "ix_daily_quest_offers_player_telegram_user_id",
        table_name="daily_quest_offers",
    )
    op.drop_table("daily_quest_offers")
