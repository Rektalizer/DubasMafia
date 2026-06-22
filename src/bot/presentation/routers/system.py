from datetime import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.application.services.system_service import SystemService
from bot.infrastructure.clock import SystemClock


def create_system_router(
    system_service: SystemService,
    clock: SystemClock,
    test_round_anchor: datetime | None,
) -> Router:
    router = Router(name="system")

    @router.message(Command("ping"))
    async def ping_handler(message: Message) -> None:
        await message.answer("pong")

    @router.message(Command("status"))
    async def status_handler(message: Message) -> None:
        text = system_service.status_text(now=clock.now_utc(), test_round_anchor=test_round_anchor)
        await message.answer(text)

    @router.message(Command("time_left"))
    async def time_left_handler(message: Message) -> None:
        text = system_service.time_left_text(now=clock.now_utc(), test_round_anchor=test_round_anchor)
        await message.answer(text)

    return router
