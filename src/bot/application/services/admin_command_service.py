from collections.abc import Awaitable, Callable
from datetime import datetime
from zoneinfo import ZoneInfo

from bot.application.ports.player_repository import PlayerRepository
from bot.application.services.offer_scheduler_service import OfferSchedulerService
from bot.application.services.quest_catalog_service import QuestCatalogService
from bot.application.services.round_settlement_service import RoundSettlementService
from bot.domain.player import Player
from bot.domain.quest import DailyQuestOffer

OfferSender = Callable[[Player, DailyQuestOffer], Awaitable[None]]


class AdminCommandService:
    def __init__(
        self,
        admin_user_ids: set[int],
        offer_scheduler_service: OfferSchedulerService,
        settlement_service: RoundSettlementService,
        player_repo: PlayerRepository,
        quest_catalog_service: QuestCatalogService,
        timezone_name: str,
    ) -> None:
        self._admin_user_ids = admin_user_ids
        self._offer_scheduler_service = offer_scheduler_service
        self._settlement_service = settlement_service
        self._player_repo = player_repo
        self._quest_catalog_service = quest_catalog_service
        self._timezone = ZoneInfo(timezone_name)

    def is_admin(self, user_id: int) -> bool:
        return user_id in self._admin_user_ids

    def admin_ids_count(self) -> int:
        return len(self._admin_user_ids)

    async def admin_send_quests_now(self, requester_user_id: int, offer_sender: OfferSender) -> str:
        if not self.is_admin(requester_user_id):
            return "Недостаточно прав для админ-команды."
        now = datetime.now(self._timezone)
        sent_count = await self._offer_scheduler_service.dispatch_offers_now(
            now=now,
            offer_sender=offer_sender,
        )
        return f"Отправка квестов выполнена. Отправлено: {sent_count}."

    async def admin_check_now(self, requester_user_id: int) -> str:
        if not self.is_admin(requester_user_id):
            return "Недостаточно прав для админ-команды."
        now = datetime.now(self._timezone)
        report = await self._settlement_service.settle_now(now=now)
        if report is None:
            return "Проверка запущена, но изменений нет."
        return report

    async def admin_reload_quests(self, requester_user_id: int) -> str:
        if not self.is_admin(requester_user_id):
            return "Недостаточно прав для админ-команды."
        quests = self._quest_catalog_service.load_enabled()
        return f"Квесты перезагружены. Активных квестов: {len(quests)}."

    async def admin_give(self, requester_user_id: int, target_username: str, amount: int, reason: str) -> str:
        if not self.is_admin(requester_user_id):
            return "Недостаточно прав для админ-команды."
        if amount <= 0:
            return "Сумма должна быть больше нуля."
        target = await self._player_repo.get_by_username(target_username)
        if target is None:
            return "Игрок не найден."
        updated = await self._player_repo.apply_balance_change(
            telegram_user_id=target.telegram_user_id,
            amount=amount,
            reason=f"admin_give:{reason}",
        )
        if updated is None:
            return "Не удалось обновить баланс."
        return f"Начислено {amount} DUB для @{target_username}. Баланс @{target_username}: {updated.balance_dub} DUB."

    async def admin_take(self, requester_user_id: int, target_username: str, amount: int, reason: str) -> str:
        if not self.is_admin(requester_user_id):
            return "Недостаточно прав для админ-команды."
        if amount <= 0:
            return "Сумма должна быть больше нуля."
        target = await self._player_repo.get_by_username(target_username)
        if target is None:
            return "Игрок не найден."
        updated = await self._player_repo.apply_balance_change(
            telegram_user_id=target.telegram_user_id,
            amount=-amount,
            reason=f"admin_take:{reason}",
        )
        if updated is None:
            return "Не удалось обновить баланс."
        return f"Списано {amount} DUB у @{target_username}. Баланс @{target_username}: {updated.balance_dub} DUB."

    async def admin_set_balance(self, requester_user_id: int, target_username: str, amount: int) -> str:
        if not self.is_admin(requester_user_id):
            return "Недостаточно прав для админ-команды."
        if amount < 0:
            return "Баланс не может быть отрицательным."
        target = await self._player_repo.get_by_username(target_username)
        if target is None:
            return "Игрок не найден."
        updated = await self._player_repo.set_balance(
            telegram_user_id=target.telegram_user_id,
            new_balance=amount,
            reason="admin_set_balance",
        )
        if updated is None:
            return "Не удалось обновить баланс."
        return f"Баланс @{target_username} установлен: {updated.balance_dub} DUB."
