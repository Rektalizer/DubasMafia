from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.infrastructure.db.models import JackpotContributionModel, JackpotStateModel


class SQLAlchemyJackpotRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_contribution(self, quest_date: date, telegram_user_id: int) -> int:
        async with self._session_factory() as session:
            query = select(JackpotContributionModel).where(
                JackpotContributionModel.quest_date == quest_date,
                JackpotContributionModel.telegram_user_id == telegram_user_id,
            )
            result = await session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                return 0
            return model.amount

    async def add_contribution(self, quest_date: date, telegram_user_id: int, amount: int) -> int:
        async with self._session_factory() as session:
            query = select(JackpotContributionModel).where(
                JackpotContributionModel.quest_date == quest_date,
                JackpotContributionModel.telegram_user_id == telegram_user_id,
            )
            result = await session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                model = JackpotContributionModel(
                    quest_date=quest_date,
                    telegram_user_id=telegram_user_id,
                    amount=amount,
                    created_at=datetime.now(UTC),
                )
                session.add(model)
            else:
                model.amount += amount
            await session.commit()
            return model.amount

    async def get_total_for_date(self, quest_date: date) -> int:
        async with self._session_factory() as session:
            total_result = await session.execute(
                select(func.sum(JackpotContributionModel.amount)).where(
                    JackpotContributionModel.quest_date == quest_date
                )
            )
            carryover = await self.get_carryover()
            return int(total_result.scalar() or 0) + carryover

    async def get_carryover(self) -> int:
        async with self._session_factory() as session:
            query = select(JackpotStateModel).where(JackpotStateModel.id == 1)
            result = await session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                return 0
            return model.carryover_amount

    async def set_carryover(self, amount: int) -> None:
        async with self._session_factory() as session:
            query = select(JackpotStateModel).where(JackpotStateModel.id == 1)
            result = await session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                session.add(JackpotStateModel(id=1, carryover_amount=amount))
            else:
                model.carryover_amount = amount
            await session.commit()
