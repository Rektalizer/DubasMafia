from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import Router
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import ChatPermissions, Message

from bot.application.services.shop_service import ShopService


def create_shop_router(
    shop_service: ShopService,
    timezone_name: str,
    group_chat_id: int,
    admin_user_ids: set[int],
) -> Router:
    router = Router(name="shop")

    @router.message(Command("shop"))
    async def shop_handler(message: Message) -> None:
        text = await shop_service.shop_text()
        await message.answer(text)

    @router.message(Command("buy"))
    async def buy_handler(message: Message) -> None:
        if message.from_user is None:
            return
        parts = (message.text or "").split()
        if len(parts) < 2:
            await message.answer("Формат: /buy shield|double|jackpot amount")
            return
        item = parts[1].lower()
        now = datetime.now(ZoneInfo(timezone_name))

        if item == "shield":
            text = await shop_service.buy_shield(telegram_user_id=message.from_user.id)
            await message.answer(text)
            return
        if item == "double":
            text = await shop_service.buy_double(
                telegram_user_id=message.from_user.id,
                now=now,
            )
            await message.answer(text)
            return
        if item == "reroll":
            text = await shop_service.buy_reroll(
                telegram_user_id=message.from_user.id,
                now=now,
            )
            await message.answer(text)
            return
        if item == "hint":
            if len(parts) < 3:
                await message.answer("Формат: /buy hint @username")
                return
            target = parts[2].lstrip("@")
            text = await shop_service.buy_hint(
                buyer_telegram_user_id=message.from_user.id,
                target_username=target,
                now=now,
            )
            await message.answer(text)
            return
        if item == "jackpot":
            if len(parts) < 3:
                await message.answer("Формат: /buy jackpot amount")
                return
            try:
                amount = int(parts[2])
            except ValueError:
                await message.answer("amount должен быть числом.")
                return
            text = await shop_service.buy_jackpot(
                telegram_user_id=message.from_user.id,
                amount=amount,
                now=now,
            )
            await message.answer(text)
            return
        if item == "mute":
            if len(parts) < 3:
                await message.answer("Формат: /buy mute @username")
                return
            target = parts[2].lstrip("@")

            async def mute_executor(chat_id: int, target_user_id: int, duration_minutes: int) -> bool:
                try:
                    until = datetime.now(ZoneInfo(timezone_name)).timestamp() + duration_minutes * 60
                    await message.bot.restrict_chat_member(
                        chat_id=chat_id,
                        user_id=target_user_id,
                        permissions=ChatPermissions(),
                        until_date=int(until),
                    )
                    return True
                except (TelegramBadRequest, TelegramForbiddenError):
                    return False

            text = await shop_service.buy_mute(
                buyer_telegram_user_id=message.from_user.id,
                target_username=target,
                now=now,
                group_chat_id=group_chat_id,
                bot_telegram_user_id=(await message.bot.get_me()).id,
                admin_user_ids=admin_user_ids,
                mute_executor=mute_executor,
            )
            await message.answer(text)
            return

        await message.answer("Пока поддерживаются: reroll, hint, shield, double, mute, jackpot.")

    return router
