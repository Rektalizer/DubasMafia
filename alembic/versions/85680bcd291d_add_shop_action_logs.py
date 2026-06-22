"""add shop action logs

Revision ID: 85680bcd291d
Revises: e096515e9d6e
Create Date: 2026-06-22 20:34:48.603795

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '85680bcd291d'
down_revision: Union[str, Sequence[str], None] = 'e096515e9d6e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "shop_actions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("action_type", sa.String(length=32), nullable=False),
        sa.Column("buyer_telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("target_telegram_user_id", sa.BigInteger(), nullable=True),
        sa.Column("result", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_shop_actions_action_type", "shop_actions", ["action_type"])
    op.create_index("ix_shop_actions_buyer_telegram_user_id", "shop_actions", ["buyer_telegram_user_id"])
    op.create_index("ix_shop_actions_target_telegram_user_id", "shop_actions", ["target_telegram_user_id"])
    op.create_index("ix_shop_actions_created_at", "shop_actions", ["created_at"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_shop_actions_created_at", table_name="shop_actions")
    op.drop_index("ix_shop_actions_target_telegram_user_id", table_name="shop_actions")
    op.drop_index("ix_shop_actions_buyer_telegram_user_id", table_name="shop_actions")
    op.drop_index("ix_shop_actions_action_type", table_name="shop_actions")
    op.drop_table("shop_actions")
