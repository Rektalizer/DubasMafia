from datetime import datetime

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.infrastructure.db.models import ShopActionModel


class SQLAlchemyShopActionRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_last_action_at(self, action_type: str, target_telegram_user_id: int) -> datetime | None:
        async with self._session_factory() as session:
            query = (
                select(ShopActionModel)
                .where(
                    ShopActionModel.action_type == action_type,
                    ShopActionModel.target_telegram_user_id == target_telegram_user_id,
                )
                .order_by(desc(ShopActionModel.created_at))
                .limit(1)
            )
            result = await session.execute(query)
            model = result.scalar_one_or_none()
            return model.created_at if model else None

    async def add_action(
        self,
        action_type: str,
        buyer_telegram_user_id: int,
        target_telegram_user_id: int | None,
        result: str,
        created_at: datetime,
    ) -> None:
        async with self._session_factory() as session:
            session.add(
                ShopActionModel(
                    action_type=action_type,
                    buyer_telegram_user_id=buyer_telegram_user_id,
                    target_telegram_user_id=target_telegram_user_id,
                    result=result,
                    created_at=created_at,
                )
            )
            await session.commit()
