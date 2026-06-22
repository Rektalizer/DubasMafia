from dataclasses import dataclass
from datetime import datetime

import pytest

from bot.application.services.admin_command_service import AdminCommandService


@dataclass
class StubOfferScheduler:
    called: bool = False

    async def dispatch_offers_now(self, now: datetime, offer_sender) -> int:
        del now, offer_sender
        self.called = True
        return 3


@dataclass
class StubSettlementService:
    called: bool = False

    async def settle_now(self, now: datetime) -> str | None:
        del now
        self.called = True
        return "report"


@dataclass
class StubPlayerRepo:
    async def get_by_username(self, username: str):  # type: ignore[no-untyped-def]
        del username
        return None

    async def apply_balance_change(self, telegram_user_id: int, amount: int, reason: str):  # type: ignore[no-untyped-def]
        del telegram_user_id, amount, reason
        return None

    async def set_balance(self, telegram_user_id: int, new_balance: int, reason: str):  # type: ignore[no-untyped-def]
        del telegram_user_id, new_balance, reason
        return None


@dataclass
class StubQuestCatalog:
    def load_enabled(self):  # type: ignore[no-untyped-def]
        return []


@pytest.mark.asyncio
async def test_admin_command_denied_for_non_admin() -> None:
    service = AdminCommandService(
        admin_user_ids={1},
        offer_scheduler_service=StubOfferScheduler(),
        settlement_service=StubSettlementService(),
        player_repo=StubPlayerRepo(),
        quest_catalog_service=StubQuestCatalog(),
        timezone_name="Europe/Moscow",
    )
    text = await service.admin_send_quests_now(requester_user_id=2, offer_sender=lambda *_: None)
    assert "Недостаточно прав" in text


@pytest.mark.asyncio
async def test_admin_command_runs_for_admin() -> None:
    service = AdminCommandService(
        admin_user_ids={1},
        offer_scheduler_service=StubOfferScheduler(),
        settlement_service=StubSettlementService(),
        player_repo=StubPlayerRepo(),
        quest_catalog_service=StubQuestCatalog(),
        timezone_name="Europe/Moscow",
    )
    text = await service.admin_send_quests_now(requester_user_id=1, offer_sender=lambda *_: None)
    assert "Отправка квестов выполнена" in text
