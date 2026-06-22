from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.application.ports.admin_read_repository import AdminLogEvent, AdminReadRepository, DailyQuestStats
from bot.infrastructure.db.models import (
    ChatMessageModel,
    DailyQuestOfferModel,
    DubTransactionModel,
    JackpotContributionModel,
    JackpotStateModel,
    PlayerModel,
    ShopActionModel,
)


class SQLAlchemyAdminReadRepository(AdminReadRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def count_players(self) -> int:
        async with self._session_factory() as session:
            result = await session.execute(select(func.count(PlayerModel.id)))
            return int(result.scalar() or 0)

    async def count_players_with_private_chat(self) -> int:
        async with self._session_factory() as session:
            result = await session.execute(
                select(func.count(PlayerModel.id)).where(PlayerModel.private_chat_id.is_not(None))
            )
            return int(result.scalar() or 0)

    async def get_daily_quest_stats(self, quest_date: date) -> DailyQuestStats:
        async with self._session_factory() as session:
            active = await session.execute(
                select(func.count(DailyQuestOfferModel.id)).where(DailyQuestOfferModel.quest_date == quest_date)
            )
            selected = await session.execute(
                select(func.count(DailyQuestOfferModel.id)).where(
                    DailyQuestOfferModel.quest_date == quest_date,
                    DailyQuestOfferModel.selected_quest_id.is_not(None),
                )
            )
            revealed = await session.execute(
                select(func.count(DailyQuestOfferModel.id)).where(
                    DailyQuestOfferModel.quest_date == quest_date,
                    DailyQuestOfferModel.status == "revealed",
                )
            )
            return DailyQuestStats(
                active_quests=int(active.scalar() or 0),
                selected_quests=int(selected.scalar() or 0),
                revealed_quests=int(revealed.scalar() or 0),
            )

    async def count_messages_between(self, start_at: datetime, end_at: datetime) -> int:
        async with self._session_factory() as session:
            result = await session.execute(
                select(func.count(ChatMessageModel.id)).where(
                    ChatMessageModel.created_at >= start_at,
                    ChatMessageModel.created_at < end_at,
                )
            )
            return int(result.scalar() or 0)

    async def get_jackpot_total_for_date(self, quest_date: date) -> int:
        async with self._session_factory() as session:
            day_total_result = await session.execute(
                select(func.sum(JackpotContributionModel.amount)).where(
                    JackpotContributionModel.quest_date == quest_date
                )
            )
            carryover_result = await session.execute(
                select(JackpotStateModel.carryover_amount).where(JackpotStateModel.id == 1)
            )
            day_total = int(day_total_result.scalar() or 0)
            carryover = int(carryover_result.scalar() or 0)
            return day_total + carryover

    async def list_recent_events(self, limit: int) -> list[AdminLogEvent]:
        async with self._session_factory() as session:
            tx_result = await session.execute(
                select(
                    DubTransactionModel.created_at,
                    PlayerModel.username,
                    DubTransactionModel.amount,
                    DubTransactionModel.reason,
                )
                .join(PlayerModel, PlayerModel.id == DubTransactionModel.player_id)
                .order_by(DubTransactionModel.created_at.desc())
                .limit(limit)
            )
            tx_rows = tx_result.all()

            accepted_result = await session.execute(
                select(
                    DailyQuestOfferModel.accepted_at,
                    DailyQuestOfferModel.player_telegram_user_id,
                    DailyQuestOfferModel.selected_quest_id,
                )
                .where(DailyQuestOfferModel.accepted_at.is_not(None))
                .order_by(DailyQuestOfferModel.accepted_at.desc())
                .limit(limit)
            )
            accepted_rows = accepted_result.all()

            shop_actions_result = await session.execute(
                select(
                    ShopActionModel.created_at,
                    ShopActionModel.action_type,
                    ShopActionModel.buyer_telegram_user_id,
                    ShopActionModel.target_telegram_user_id,
                    ShopActionModel.result,
                )
                .order_by(ShopActionModel.created_at.desc())
                .limit(limit)
            )
            shop_action_rows = shop_actions_result.all()

        events: list[AdminLogEvent] = []
        for ts, username, amount, reason in tx_rows:
            name = f"@{username}" if username else "player"
            events.append(
                AdminLogEvent(
                    timestamp=ts,
                    message=f"DUB txn {name}: {amount:+d} ({reason})",
                )
            )
        for ts, player_telegram_user_id, quest_id in accepted_rows:
            events.append(
                AdminLogEvent(
                    timestamp=ts,
                    message=f"quest accepted by {player_telegram_user_id}: {quest_id}",
                )
            )
        for ts, action_type, buyer_id, target_id, result in shop_action_rows:
            target_part = f", target={target_id}" if target_id is not None else ""
            events.append(
                AdminLogEvent(
                    timestamp=ts,
                    message=(
                        f"shop action {action_type}: buyer={buyer_id}{target_part}, "
                        f"result={result}"
                    ),
                )
            )

        events.sort(key=lambda item: item.timestamp, reverse=True)
        return events[:limit]
