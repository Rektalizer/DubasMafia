from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot.application.services.admin_command_service import AdminCommandService, OfferSender
from bot.application.services.admin_observability_service import AdminObservabilityService


def create_admin_router(
    admin_command_service: AdminCommandService,
    admin_observability_service: AdminObservabilityService,
    offer_sender: OfferSender,
    group_chat_id: int,
) -> Router:
    router = Router(name="admin")

    @router.message(Command("admin_send_quests_now"))
    async def admin_send_quests_now_handler(message: Message) -> None:
        if message.from_user is None:
            return
        text = await admin_command_service.admin_send_quests_now(
            requester_user_id=message.from_user.id,
            offer_sender=offer_sender,
        )
        await message.answer(text)

    @router.message(Command("admin_check_now"))
    async def admin_check_now_handler(message: Message) -> None:
        if message.from_user is None:
            return
        text = await admin_command_service.admin_check_now(
            requester_user_id=message.from_user.id,
        )
        await message.answer(text)

    @router.message(Command("admin_status"))
    async def admin_status_handler(message: Message) -> None:
        if message.from_user is None:
            return
        text = await admin_observability_service.admin_status(
            requester_user_id=message.from_user.id,
        )
        await message.answer(text)

    @router.message(Command("admin_logs"))
    async def admin_logs_handler(message: Message) -> None:
        if message.from_user is None:
            return
        text = await admin_observability_service.admin_logs(
            requester_user_id=message.from_user.id,
        )
        await message.answer(text)

    @router.message(Command("admin_reload_quests"))
    async def admin_reload_quests_handler(message: Message) -> None:
        if message.from_user is None:
            return
        text = await admin_command_service.admin_reload_quests(
            requester_user_id=message.from_user.id,
        )
        await message.answer(text)

    @router.message(Command("admin_give"))
    async def admin_give_handler(message: Message) -> None:
        if message.from_user is None:
            return
        parts = (message.text or "").split(maxsplit=3)
        if len(parts) < 4:
            await message.answer("Формат: /admin_give @user amount reason")
            return
        target = parts[1].lstrip("@")
        try:
            amount = int(parts[2])
        except ValueError:
            await message.answer("amount должен быть числом.")
            return
        reason = parts[3]
        text = await admin_command_service.admin_give(
            requester_user_id=message.from_user.id,
            target_username=target,
            amount=amount,
            reason=reason,
        )
        await message.answer(text)

    @router.message(Command("admin_take"))
    async def admin_take_handler(message: Message) -> None:
        if message.from_user is None:
            return
        parts = (message.text or "").split(maxsplit=3)
        if len(parts) < 4:
            await message.answer("Формат: /admin_take @user amount reason")
            return
        target = parts[1].lstrip("@")
        try:
            amount = int(parts[2])
        except ValueError:
            await message.answer("amount должен быть числом.")
            return
        reason = parts[3]
        text = await admin_command_service.admin_take(
            requester_user_id=message.from_user.id,
            target_username=target,
            amount=amount,
            reason=reason,
        )
        await message.answer(text)

    @router.message(Command("admin_set_balance"))
    async def admin_set_balance_handler(message: Message) -> None:
        if message.from_user is None:
            return
        parts = (message.text or "").split(maxsplit=2)
        if len(parts) < 3:
            await message.answer("Формат: /admin_set_balance @user amount")
            return
        target = parts[1].lstrip("@")
        try:
            amount = int(parts[2])
        except ValueError:
            await message.answer("amount должен быть числом.")
            return
        text = await admin_command_service.admin_set_balance(
            requester_user_id=message.from_user.id,
            target_username=target,
            amount=amount,
        )
        await message.answer(text)

    @router.message(Command("admin_broadcast"))
    async def admin_broadcast_handler(message: Message) -> None:
        if message.from_user is None:
            return
        if not admin_command_service.is_admin(message.from_user.id):
            await message.answer("Недостаточно прав для админ-команды.")
            return
        parts = (message.text or "").split(maxsplit=1)
        if len(parts) < 2 or not parts[1].strip():
            await message.answer("Формат: /admin_broadcast текст")
            return
        text = parts[1].strip()
        await message.bot.send_message(chat_id=group_chat_id, text=text)
        await message.answer("Сообщение отправлено в игровой чат.")

    @router.message(Command("whoami"))
    async def whoami_handler(message: Message) -> None:
        if message.from_user is None:
            return
        username = f"@{message.from_user.username}" if message.from_user.username else "нет"
        is_admin = admin_command_service.is_admin(message.from_user.id)
        await message.answer(
            "whoami\n"
            f"user_id={message.from_user.id}\n"
            f"username={username}\n"
            f"admin={'yes' if is_admin else 'no'}\n"
            f"configured_admin_ids={admin_command_service.admin_ids_count()}"
        )

    return router
