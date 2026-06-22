from datetime import UTC, datetime

from datetime import date

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PlayerModel(Base):
    __tablename__ = "players"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    private_chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    balance_dub: Mapped[int] = mapped_column(Integer, default=0)
    shield_count: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(default=True)
    is_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )


class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_message_id: Mapped[int] = mapped_column(BigInteger, index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    author_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    author_username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    replied_message_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    replied_author_user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class DubTransactionModel(Base):
    __tablename__ = "dub_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id"), index=True)
    amount: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(64))
    related_daily_quest_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    related_purchase_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    balance_after: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )


class DailyQuestOfferModel(Base):
    __tablename__ = "daily_quest_offers"
    __table_args__ = (UniqueConstraint("player_telegram_user_id", "quest_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    player_telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    quest_date: Mapped[date] = mapped_column(Date, index=True)
    options_json: Mapped[list[dict]] = mapped_column(JSON)
    selected_difficulty: Mapped[str | None] = mapped_column(String(16), nullable=True)
    selected_quest_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="offered")
    double_active: Mapped[bool] = mapped_column(default=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class JackpotContributionModel(Base):
    __tablename__ = "jackpot_contributions"
    __table_args__ = (UniqueConstraint("quest_date", "telegram_user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quest_date: Mapped[date] = mapped_column(Date, index=True)
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    amount: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )


class JackpotStateModel(Base):
    __tablename__ = "jackpot_state"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    carryover_amount: Mapped[int] = mapped_column(Integer, default=0)


class ShopActionModel(Base):
    __tablename__ = "shop_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    action_type: Mapped[str] = mapped_column(String(32), index=True)
    buyer_telegram_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    target_telegram_user_id: Mapped[int | None] = mapped_column(BigInteger, index=True, nullable=True)
    result: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
