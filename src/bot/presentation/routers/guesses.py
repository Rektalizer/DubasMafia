from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.application.services.guess_service import GuessService


def create_guess_router(guess_service: GuessService, timezone_name: str) -> Router:
    router = Router(name="guesses")

    @router.message(Command("guess"))
    async def guess_handler(message: Message) -> None:
        if message.from_user is None:
            return
        if message.chat.type == "private":
            await message.answer("Команду /guess используй в игровом чате.")
            return
        parts = (message.text or "").split(maxsplit=2)
        if len(parts) < 3:
            await message.answer("Формат: /guess @username текст догадки")
            return

        target = parts[1].strip()
        if target.startswith("@"):
            target = target[1:]
        guess_text = parts[2]
        text = await guess_service.process_guess(
            guesser_telegram_user_id=message.from_user.id,
            target_username=target,
            guess_text=guess_text,
            now=datetime.now(ZoneInfo(timezone_name)),
        )
        await message.answer(text)

    return router
