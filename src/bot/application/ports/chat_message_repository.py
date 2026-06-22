from typing import Protocol
from datetime import datetime

from bot.domain.chat_message import ChatMessage


class ChatMessageRepository(Protocol):
    async def save(self, message: ChatMessage) -> None:
        ...

    async def has_message_in_window(
        self,
        chat_id: int,
        author_user_id: int,
        start_at: datetime,
        end_at: datetime,
    ) -> bool:
        ...

    async def list_messages_in_window(
        self,
        chat_id: int,
        author_user_id: int,
        start_at: datetime,
        end_at: datetime,
    ) -> list[ChatMessage]:
        ...
