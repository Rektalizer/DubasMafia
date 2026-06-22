from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.application.services.player_service import PlayerService


def create_player_router(player_service: PlayerService) -> Router:
    router = Router(name="players")

    @router.message(Command("join"))
    async def join_handler(message: Message) -> None:
        if message.from_user is None:
            return
        if message.chat.type == "private":
            await message.answer("Команду /join нужно использовать в игровом групповом чате.")
            return

        text = await player_service.join(
            telegram_user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
        )
        await message.answer(text)

    @router.message(Command("start"))
    async def start_handler(message: Message) -> None:
        if message.from_user is None:
            return
        if message.chat.type != "private":
            await message.answer("Команду /start нужно использовать в личке с ботом.")
            return

        text = await player_service.connect_private_chat(
            telegram_user_id=message.from_user.id,
            private_chat_id=message.chat.id,
        )
        await message.answer(text)

    @router.message(Command("wallet"))
    async def wallet_handler(message: Message) -> None:
        if message.from_user is None:
            return
        text = await player_service.wallet_text(telegram_user_id=message.from_user.id)
        await message.answer(text)

    @router.message(Command("leaderboard"))
    async def leaderboard_handler(message: Message) -> None:
        if message.from_user is None:
            return
        text = await player_service.leaderboard_text(current_telegram_user_id=message.from_user.id)
        await message.answer(text)

    return router
