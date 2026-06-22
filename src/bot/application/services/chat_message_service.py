from bot.application.ports.chat_message_repository import ChatMessageRepository
from bot.domain.chat_message import ChatMessage


class ChatMessageService:
    def __init__(self, repo: ChatMessageRepository) -> None:
        self._repo = repo

    async def save_message(self, message: ChatMessage) -> None:
        await self._repo.save(message=message)
