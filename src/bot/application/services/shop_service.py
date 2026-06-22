from dataclasses import dataclass
from datetime import datetime, timedelta
from collections.abc import Awaitable, Callable

from bot.application.services.daily_quest_service import DailyQuestService
from bot.application.ports.shop_action_repository import ShopActionRepository
from bot.application.services.quest_catalog_service import QuestCatalogService
from bot.application.ports.daily_quest_repository import DailyQuestRepository
from bot.application.ports.jackpot_repository import JackpotRepository
from bot.application.ports.player_repository import PlayerRepository
from bot.application.services.schedule_service import ScheduleService


@dataclass(frozen=True, slots=True)
class ShopSettings:
    shield_price: int
    double_price: int
    reroll_price: int
    hint_price: int
    mute_price: int
    mute_duration_minutes: int
    mute_cooldown_minutes: int
    jackpot_min: int
    jackpot_max_per_day: int

MuteExecutor = Callable[[int, int, int], Awaitable[bool]]


class ShopService:
    def __init__(
        self,
        player_repo: PlayerRepository,
        daily_quest_repo: DailyQuestRepository,
        jackpot_repo: JackpotRepository,
        daily_quest_service: DailyQuestService,
        quest_catalog_service: QuestCatalogService,
        shop_action_repo: ShopActionRepository,
        schedule_service: ScheduleService,
        settings: ShopSettings,
        test_round_anchor: datetime | None,
    ) -> None:
        self._player_repo = player_repo
        self._daily_quest_repo = daily_quest_repo
        self._jackpot_repo = jackpot_repo
        self._daily_quest_service = daily_quest_service
        self._quest_catalog_service = quest_catalog_service
        self._shop_action_repo = shop_action_repo
        self._schedule_service = schedule_service
        self._settings = settings
        self._test_round_anchor = test_round_anchor

    async def shop_text(self) -> str:
        return (
            "🛒 Магазин DUB\n"
            f"/buy reroll — {self._settings.reroll_price} DUB\n"
            f"/buy hint @user — {self._settings.hint_price} DUB\n"
            f"/buy shield — {self._settings.shield_price} DUB\n"
            f"/buy double — {self._settings.double_price} DUB\n"
            f"/buy mute @user — {self._settings.mute_price} DUB\n"
            f"/buy jackpot amount — min {self._settings.jackpot_min} DUB"
        )

    async def buy_mute(
        self,
        buyer_telegram_user_id: int,
        target_username: str,
        now: datetime,
        group_chat_id: int,
        bot_telegram_user_id: int,
        admin_user_ids: set[int],
        mute_executor: MuteExecutor,
    ) -> str:
        buyer = await self._player_repo.get_by_telegram_user_id(buyer_telegram_user_id)
        if buyer is None:
            return "Сначала подключись к игре через /join."
        if buyer.balance_dub < self._settings.mute_price:
            return "Недостаточно DUB для покупки mute."

        target = await self._player_repo.get_by_username(target_username)
        if target is None:
            return "Игрок не найден."
        if target.telegram_user_id == buyer_telegram_user_id:
            return "Нельзя мутить самого себя."
        if target.telegram_user_id == bot_telegram_user_id:
            return "Нельзя мутить бота."
        if target.telegram_user_id in admin_user_ids:
            return "Нельзя мутить админов."
        if not target.is_active:
            return "Нельзя мутить игрока, который не участвует в игре."

        last_mute = await self._shop_action_repo.get_last_action_at(
            action_type="mute",
            target_telegram_user_id=target.telegram_user_id,
        )
        if last_mute and now - last_mute < timedelta(minutes=self._settings.mute_cooldown_minutes):
            return "Этого игрока уже мутили недавно. Попробуй позже."

        if target.shield_count > 0:
            await self._player_repo.apply_balance_change(
                telegram_user_id=buyer_telegram_user_id,
                amount=-self._settings.mute_price,
                reason="shop_mute_shield_blocked",
            )
            await self._player_repo.add_shield(telegram_user_id=target.telegram_user_id, delta=-1)
            await self._shop_action_repo.add_action(
                action_type="mute",
                buyer_telegram_user_id=buyer_telegram_user_id,
                target_telegram_user_id=target.telegram_user_id,
                result="blocked_by_shield",
                created_at=now,
            )
            return (
                f"🛡 @{buyer.username or buyer.telegram_user_id} попытался замутить "
                f"@{target.username or target.telegram_user_id}, но щит спас цель."
            )

        muted = await mute_executor(
            group_chat_id,
            target.telegram_user_id,
            self._settings.mute_duration_minutes,
        )
        if not muted:
            return "Я не могу замутить игрока: у меня нет нужных прав администратора."

        await self._player_repo.apply_balance_change(
            telegram_user_id=buyer_telegram_user_id,
            amount=-self._settings.mute_price,
            reason="shop_mute",
        )
        await self._shop_action_repo.add_action(
            action_type="mute",
            buyer_telegram_user_id=buyer_telegram_user_id,
            target_telegram_user_id=target.telegram_user_id,
            result="muted",
            created_at=now,
        )
        return (
            f"🔇 @{buyer.username or buyer.telegram_user_id} купил mute для "
            f"@{target.username or target.telegram_user_id} на {self._settings.mute_duration_minutes} минут."
        )

    async def buy_reroll(self, telegram_user_id: int, now: datetime) -> str:
        player = await self._player_repo.get_by_telegram_user_id(telegram_user_id)
        if player is None:
            return "Сначала подключись к игре через /join."
        if player.balance_dub < self._settings.reroll_price:
            return "Недостаточно DUB для покупки reroll."

        window = self._schedule_service.current_window(now=now, test_round_anchor=self._test_round_anchor)
        offer = await self._daily_quest_repo.get_offer(
            player_telegram_user_id=telegram_user_id,
            quest_date=window.offer_at.date(),
        )
        if offer is not None and offer.status == "accepted":
            return "Ты уже выбрал квест на сегодня. Reroll больше недоступен."

        templates = self._quest_catalog_service.load_enabled()
        await self._daily_quest_service.create_offer_for_player(
            player_telegram_user_id=telegram_user_id,
            quest_date=window.offer_at.date(),
            quest_templates=templates,
        )
        await self._player_repo.apply_balance_change(
            telegram_user_id=telegram_user_id,
            amount=-self._settings.reroll_price,
            reason="shop_reroll",
        )
        return "🔄 Reroll выполнен. Варианты квестов обновлены."

    async def buy_hint(self, buyer_telegram_user_id: int, target_username: str, now: datetime) -> str:
        buyer = await self._player_repo.get_by_telegram_user_id(buyer_telegram_user_id)
        if buyer is None:
            return "Сначала подключись к игре через /join."
        if buyer.balance_dub < self._settings.hint_price:
            return "Недостаточно DUB для покупки hint."
        target = await self._player_repo.get_by_username(target_username)
        if target is None:
            return "Игрок не найден."
        if target.telegram_user_id == buyer_telegram_user_id:
            return "Нельзя покупать hint на самого себя."

        window = self._schedule_service.current_window(now=now, test_round_anchor=self._test_round_anchor)
        offer = await self._daily_quest_repo.get_offer(
            player_telegram_user_id=target.telegram_user_id,
            quest_date=window.offer_at.date(),
        )
        if offer is None or offer.status == "offered":
            return "У этого игрока сейчас нет активного квеста."
        if offer.status == "revealed":
            return "Этот квест уже раскрыт."
        if offer.selected_quest_id is None:
            return "У этого игрока сейчас нет активного квеста."

        selected = next((item for item in offer.options if item.quest_id == offer.selected_quest_id), None)
        if selected is None:
            return "У этого игрока сейчас нет активного квеста."

        hint = selected.hint_text or self._build_hint(selected.validation_rule.validation_type)
        await self._player_repo.apply_balance_change(
            telegram_user_id=buyer_telegram_user_id,
            amount=-self._settings.hint_price,
            reason="shop_hint",
        )
        return f"💡 Подсказка по квесту @{target_username}: {hint}"

    async def buy_shield(self, telegram_user_id: int) -> str:
        player = await self._player_repo.get_by_telegram_user_id(telegram_user_id)
        if player is None:
            return "Сначала подключись к игре через /join."
        if player.balance_dub < self._settings.shield_price:
            return "Недостаточно DUB для покупки shield."
        await self._player_repo.apply_balance_change(
            telegram_user_id=telegram_user_id,
            amount=-self._settings.shield_price,
            reason="shop_shield",
        )
        updated = await self._player_repo.add_shield(telegram_user_id=telegram_user_id, delta=1)
        shields = updated.shield_count if updated else player.shield_count + 1
        return f"🛡 Shield куплен. Активных щитов: {shields}."

    async def buy_double(self, telegram_user_id: int, now: datetime) -> str:
        player = await self._player_repo.get_by_telegram_user_id(telegram_user_id)
        if player is None:
            return "Сначала подключись к игре через /join."
        if player.balance_dub < self._settings.double_price:
            return "Недостаточно DUB для покупки double."

        window = self._schedule_service.current_window(now=now, test_round_anchor=self._test_round_anchor)
        offer = await self._daily_quest_repo.get_offer(
            player_telegram_user_id=telegram_user_id,
            quest_date=window.offer_at.date(),
        )
        if offer is None or offer.status != "accepted":
            return "Для покупки double сначала прими квест на сегодня."
        if offer.double_active:
            return "Double уже активирован на сегодня."
        await self._player_repo.apply_balance_change(
            telegram_user_id=telegram_user_id,
            amount=-self._settings.double_price,
            reason="shop_double",
        )
        await self._daily_quest_repo.set_double_active(
            player_telegram_user_id=telegram_user_id,
            quest_date=window.offer_at.date(),
        )
        return "🎲 Double активирован на текущий квест."

    async def buy_jackpot(self, telegram_user_id: int, amount: int, now: datetime) -> str:
        if amount < self._settings.jackpot_min:
            return f"Минимальный вклад в jackpot: {self._settings.jackpot_min} DUB."
        player = await self._player_repo.get_by_telegram_user_id(telegram_user_id)
        if player is None:
            return "Сначала подключись к игре через /join."
        if player.balance_dub < amount:
            return "Недостаточно DUB для вклада в jackpot."

        window = self._schedule_service.current_window(now=now, test_round_anchor=self._test_round_anchor)
        current = await self._jackpot_repo.get_contribution(
            quest_date=window.offer_at.date(),
            telegram_user_id=telegram_user_id,
        )
        if current + amount > self._settings.jackpot_max_per_day:
            return (
                "Превышен лимит вклада в jackpot за день: "
                f"{self._settings.jackpot_max_per_day} DUB."
            )
        await self._player_repo.apply_balance_change(
            telegram_user_id=telegram_user_id,
            amount=-amount,
            reason="shop_jackpot",
        )
        total_for_user = await self._jackpot_repo.add_contribution(
            quest_date=window.offer_at.date(),
            telegram_user_id=telegram_user_id,
            amount=amount,
        )
        return f"🎰 Вклад в jackpot принят: {amount} DUB. Твой вклад сегодня: {total_for_user} DUB."

    @staticmethod
    def _build_hint(validation_type: str) -> str:
        if validation_type == "reply_contains_text":
            return "Квест связан с reply."
        if validation_type == "reply_to_target_contains_text":
            return "Квест связан с конкретным игроком и reply."
        if validation_type == "custom_ai_check":
            return "Квест связан с контекстом и смыслом, а не только с ключевым словом."
        return "Квест связан с ключевым словом в сообщении."
