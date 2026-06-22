from aiogram import Router
from aiogram.types import Message

from bot.application.services.chat_message_service import ChatMessageService
from bot.domain.chat_message import ChatMessage


def create_message_capture_router(chat_message_service: ChatMessageService) -> Router:
    router = Router(name="message_capture")

    @router.message()
    async def capture_message(message: Message) -> None:
        if message.chat.type == "private":
            return
        if message.from_user is None or message.from_user.is_bot:
            return

        replied_message_id = message.reply_to_message.message_id if message.reply_to_message else None
        replied_author_user_id = (
            message.reply_to_message.from_user.id
            if message.reply_to_message and message.reply_to_message.from_user
            else None
        )

        await chat_message_service.save_message(
            ChatMessage(
                telegram_message_id=message.message_id,
                chat_id=message.chat.id,
                author_user_id=message.from_user.id,
                author_username=message.from_user.username,
                text=message.text,
                replied_message_id=replied_message_id,
                replied_author_user_id=replied_author_user_id,
                created_at=message.date,
            )
        )

    return router
