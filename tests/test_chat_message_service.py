from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from bot.application.services.chat_message_service import ChatMessageService
from bot.domain.chat_message import ChatMessage


@dataclass
class InMemoryChatMessageRepo:
    saved: list[ChatMessage]

    async def save(self, message: ChatMessage) -> None:
        self.saved.append(message)


@pytest.mark.asyncio
async def test_chat_message_service_persists_message() -> None:
    repo = InMemoryChatMessageRepo(saved=[])
    service = ChatMessageService(repo=repo)
    message = ChatMessage(
        telegram_message_id=10,
        chat_id=-1001,
        author_user_id=200,
        author_username="ivan",
        text="hello",
        replied_message_id=None,
        replied_author_user_id=None,
        created_at=datetime.now(UTC),
    )

    await service.save_message(message=message)

    assert len(repo.saved) == 1
    assert repo.saved[0].telegram_message_id == 10
