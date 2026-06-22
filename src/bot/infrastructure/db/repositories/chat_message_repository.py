from datetime import datetime

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.domain.chat_message import ChatMessage
from bot.infrastructure.db.models import ChatMessageModel


class SQLAlchemyChatMessageRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def save(self, message: ChatMessage) -> None:
        async with self._session_factory() as session:
            session.add(
                ChatMessageModel(
                    telegram_message_id=message.telegram_message_id,
                    chat_id=message.chat_id,
                    author_user_id=message.author_user_id,
                    author_username=message.author_username,
                    text=message.text,
                    replied_message_id=message.replied_message_id,
                    replied_author_user_id=message.replied_author_user_id,
                    created_at=message.created_at,
                )
            )
            await session.commit()

    async def has_message_in_window(
        self,
        chat_id: int,
        author_user_id: int,
        start_at: datetime,
        end_at: datetime,
    ) -> bool:
        async with self._session_factory() as session:
            query = select(
                exists().where(
                    ChatMessageModel.chat_id == chat_id,
                    ChatMessageModel.author_user_id == author_user_id,
                    ChatMessageModel.created_at >= start_at,
                    ChatMessageModel.created_at < end_at,
                )
            )
            result = await session.execute(query)
            return bool(result.scalar())

    async def list_messages_in_window(
        self,
        chat_id: int,
        author_user_id: int,
        start_at: datetime,
        end_at: datetime,
    ) -> list[ChatMessage]:
        async with self._session_factory() as session:
            query = (
                select(ChatMessageModel)
                .where(
                    ChatMessageModel.chat_id == chat_id,
                    ChatMessageModel.author_user_id == author_user_id,
                    ChatMessageModel.created_at >= start_at,
                    ChatMessageModel.created_at < end_at,
                )
                .order_by(ChatMessageModel.created_at.asc())
            )
            result = await session.execute(query)
            models = result.scalars().all()
            return [
                ChatMessage(
                    telegram_message_id=model.telegram_message_id,
                    chat_id=model.chat_id,
                    author_user_id=model.author_user_id,
                    author_username=model.author_username,
                    text=model.text,
                    replied_message_id=model.replied_message_id,
                    replied_author_user_id=model.replied_author_user_id,
                    created_at=model.created_at,
                )
                for model in models
            ]
