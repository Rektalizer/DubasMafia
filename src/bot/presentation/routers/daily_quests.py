from datetime import datetime
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.application.services.daily_quest_service import DailyQuestService
from bot.application.services.quest_catalog_service import QuestCatalogService
from bot.application.services.schedule_service import ScheduleService
from bot.domain.quest import DailyQuestOffer, QuestDifficulty


def create_daily_quest_router(
    daily_quest_service: DailyQuestService,
    quest_catalog_service: QuestCatalogService,
    schedule_service: ScheduleService,
    timezone_name: str,
    group_chat_id: int,
    test_round_anchor: datetime | None,
) -> Router:
    router = Router(name="daily_quests")

    @router.message(Command("quests_now"))
    async def offer_now_handler(message: Message) -> None:
        if message.from_user is None:
            return
        if message.chat.type != "private":
            await message.answer("Команда /quests_now доступна в личке с ботом.")
            return

        today = datetime.now(ZoneInfo(timezone_name)).date()
        offer = await daily_quest_service.get_offer(
            player_telegram_user_id=message.from_user.id,
            quest_date=today,
        )
        if offer is None or offer.status == "accepted":
            templates = quest_catalog_service.load_enabled()
            offer = await daily_quest_service.create_offer_for_player(
                player_telegram_user_id=message.from_user.id,
                quest_date=today,
                quest_templates=templates,
            )

        await message.answer(
            build_offer_text(offer=offer),
            reply_markup=build_offer_keyboard(),
        )

    @router.callback_query(F.data.startswith("pick_quest:"))
    async def pick_quest_handler(callback: CallbackQuery) -> None:
        if callback.from_user is None:
            return
        if callback.message is None:
            return

        raw_difficulty = callback.data.split(":", maxsplit=1)[1]
        difficulty = QuestDifficulty(raw_difficulty)
        now = datetime.now(ZoneInfo(timezone_name))
        window = schedule_service.current_window(now=now, test_round_anchor=test_round_anchor)
        if now < window.offer_at or now >= window.check_at:
            await callback.answer("Сейчас вне активного окна выбора квеста.", show_alert=True)
            return
        today = window.offer_at.date()

        accepted = await daily_quest_service.accept_offer(
            player_telegram_user_id=callback.from_user.id,
            quest_date=today,
            selected_difficulty=difficulty,
        )
        if accepted is None:
            await callback.answer("Квест не найден или уже недоступен.", show_alert=True)
            return

        selected_option = next(
            item for item in accepted.options if item.quest_id == accepted.selected_quest_id
        )
        await callback.message.answer(
            "Квест принят.\n"
            f"Сложность: {selected_option.difficulty.value}\n"
            f"Возможная награда: {selected_option.base_reward} DUB\n"
            "Проверка будет в конце раунда."
        )
        await callback.bot.send_message(
            chat_id=group_chat_id,
            text=(
                f"🎭 @{callback.from_user.username or callback.from_user.id} принял секретный квест. "
                f"Теперь его можно раскрыть через /guess @{callback.from_user.username or callback.from_user.id} "
                "твоя догадка ."
            ),
        )
        await callback.answer("Квест выбран.")

    return router


def build_offer_text(offer: DailyQuestOffer) -> str:
    option_by_difficulty = {item.difficulty: item for item in offer.options}
    easy = option_by_difficulty[QuestDifficulty.EASY]
    medium = option_by_difficulty[QuestDifficulty.MEDIUM]
    hard = option_by_difficulty[QuestDifficulty.HARD]
    return (
        "🎲 Выбери тайный квест на сегодня:\n\n"
        f"Лёгкий — {easy.base_reward} DUB\n{easy.description_for_player}\n\n"
        f"Средний — {medium.base_reward} DUB\n{medium.description_for_player}\n\n"
        f"Тяжёлый — {hard.base_reward} DUB\n{hard.description_for_player}"
    )


def build_offer_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Взять лёгкий", callback_data="pick_quest:easy")],
            [InlineKeyboardButton(text="Взять средний", callback_data="pick_quest:medium")],
            [InlineKeyboardButton(text="Взять тяжёлый", callback_data="pick_quest:hard")],
        ]
    )
