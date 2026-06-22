from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.domain.player import Player
from bot.infrastructure.db.models import DubTransactionModel, PlayerModel


class SQLAlchemyPlayerRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_telegram_user_id(self, telegram_user_id: int) -> Player | None:
        async with self._session_factory() as session:
            query = select(PlayerModel).where(PlayerModel.telegram_user_id == telegram_user_id)
            result = await session.execute(query)
            model = result.scalar_one_or_none()
            return self._to_domain(model) if model else None

    async def get_by_username(self, username: str) -> Player | None:
        async with self._session_factory() as session:
            query = select(PlayerModel).where(PlayerModel.username == username)
            result = await session.execute(query)
            model = result.scalar_one_or_none()
            return self._to_domain(model) if model else None

    async def create(
        self,
        telegram_user_id: int,
        username: str | None,
        first_name: str | None,
        starting_balance: int,
    ) -> Player:
        async with self._session_factory() as session:
            model = PlayerModel(
                telegram_user_id=telegram_user_id,
                username=username,
                first_name=first_name,
                balance_dub=starting_balance,
            )
            session.add(model)
            await session.commit()
            await session.refresh(model)
            return self._to_domain(model)

    async def update_private_chat_id(self, telegram_user_id: int, private_chat_id: int) -> None:
        async with self._session_factory() as session:
            query = select(PlayerModel).where(PlayerModel.telegram_user_id == telegram_user_id)
            result = await session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                return
            model.private_chat_id = private_chat_id
            await session.commit()

    async def top_by_balance(self, limit: int) -> list[Player]:
        async with self._session_factory() as session:
            query = select(PlayerModel).order_by(desc(PlayerModel.balance_dub)).limit(limit)
            result = await session.execute(query)
            models = result.scalars().all()
            return [self._to_domain(model) for model in models]

    async def list_active_with_private_chat(self) -> list[Player]:
        async with self._session_factory() as session:
            query = select(PlayerModel).where(
                PlayerModel.is_active.is_(True),
                PlayerModel.private_chat_id.is_not(None),
            )
            result = await session.execute(query)
            models = result.scalars().all()
            return [self._to_domain(model) for model in models]

    async def apply_balance_change(self, telegram_user_id: int, amount: int, reason: str) -> Player | None:
        async with self._session_factory() as session:
            query = select(PlayerModel).where(PlayerModel.telegram_user_id == telegram_user_id)
            result = await session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                return None

            model.balance_dub += amount
            session.add(
                DubTransactionModel(
                    player_id=model.id,
                    amount=amount,
                    reason=reason,
                    balance_after=model.balance_dub,
                )
            )
            await session.commit()
            return self._to_domain(model)

    async def set_balance(self, telegram_user_id: int, new_balance: int, reason: str) -> Player | None:
        async with self._session_factory() as session:
            query = select(PlayerModel).where(PlayerModel.telegram_user_id == telegram_user_id)
            result = await session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                return None

            diff = new_balance - model.balance_dub
            model.balance_dub = new_balance
            session.add(
                DubTransactionModel(
                    player_id=model.id,
                    amount=diff,
                    reason=reason,
                    balance_after=model.balance_dub,
                )
            )
            await session.commit()
            return self._to_domain(model)

    async def add_shield(self, telegram_user_id: int, delta: int) -> Player | None:
        async with self._session_factory() as session:
            query = select(PlayerModel).where(PlayerModel.telegram_user_id == telegram_user_id)
            result = await session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                return None
            model.shield_count = max(0, model.shield_count + delta)
            await session.commit()
            return self._to_domain(model)

    @staticmethod
    def _to_domain(model: PlayerModel) -> Player:
        values = {
            "id": model.id,
            "telegram_user_id": model.telegram_user_id,
            "username": model.username,
            "first_name": model.first_name,
            "private_chat_id": model.private_chat_id,
            "balance_dub": model.balance_dub,
            "shield_count": model.shield_count,
            "is_active": model.is_active,
            "is_admin": model.is_admin,
        }
        return Player(**values)
