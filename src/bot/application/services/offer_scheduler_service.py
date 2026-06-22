from collections.abc import Awaitable, Callable
from datetime import datetime

from bot.application.ports.player_repository import PlayerRepository
from bot.application.services.daily_quest_service import DailyQuestService
from bot.application.services.quest_catalog_service import QuestCatalogService
from bot.application.services.schedule_service import ScheduleService
from bot.domain.player import Player
from bot.domain.quest import DailyQuestOffer

OfferSender = Callable[[Player, DailyQuestOffer], Awaitable[None]]


class OfferSchedulerService:
    def __init__(
        self,
        schedule_service: ScheduleService,
        daily_quest_service: DailyQuestService,
        player_repo: PlayerRepository,
        quest_catalog_service: QuestCatalogService,
        test_round_anchor: datetime | None,
    ) -> None:
        self._schedule_service = schedule_service
        self._daily_quest_service = daily_quest_service
        self._player_repo = player_repo
        self._quest_catalog_service = quest_catalog_service
        self._test_round_anchor = test_round_anchor

    async def tick(self, now: datetime, offer_sender: OfferSender) -> None:
        await self._dispatch(now=now, offer_sender=offer_sender, require_active_window=True)

    async def dispatch_offers_now(self, now: datetime, offer_sender: OfferSender) -> int:
        return await self._dispatch(now=now, offer_sender=offer_sender, require_active_window=False)

    async def _dispatch(
        self,
        now: datetime,
        offer_sender: OfferSender,
        require_active_window: bool,
    ) -> int:
        window = self._schedule_service.current_window(
            now=now,
            test_round_anchor=self._test_round_anchor,
        )
        if require_active_window and (now < window.offer_at or now >= window.check_at):
            return 0

        quest_date = window.offer_at.date()
        templates = self._quest_catalog_service.load_enabled()
        players = await self._player_repo.list_active_with_private_chat()
        sent_count = 0
        for player in players:
            existing = await self._daily_quest_service.get_offer(
                player_telegram_user_id=player.telegram_user_id,
                quest_date=quest_date,
            )
            if existing is not None:
                continue
            offer = await self._daily_quest_service.create_offer_for_player(
                player_telegram_user_id=player.telegram_user_id,
                quest_date=quest_date,
                quest_templates=templates,
            )
            await offer_sender(player, offer)
            sent_count += 1
        return sent_count
