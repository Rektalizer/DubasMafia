from dataclasses import dataclass

import pytest

from bot.application.services.admin_command_service import AdminCommandService
from bot.domain.player import Player


@dataclass
class StubOfferScheduler:
    async def dispatch_offers_now(self, now, offer_sender):  # type: ignore[no-untyped-def]
        del now, offer_sender
        return 0


@dataclass
class StubSettlement:
    async def settle_now(self, now):  # type: ignore[no-untyped-def]
        del now
        return None


@dataclass
class StubQuestCatalog:
    loaded: bool = False

    def load_enabled(self):  # type: ignore[no-untyped-def]
        self.loaded = True
        return []


@dataclass
class InMemoryPlayerRepo:
    players: dict[str, Player]

    async def get_by_username(self, username: str) -> Player | None:
        return self.players.get(username)

    async def apply_balance_change(self, telegram_user_id: int, amount: int, reason: str) -> Player | None:
        del reason
        for username, player in self.players.items():
            if player.telegram_user_id == telegram_user_id:
                updated = Player(
                    id=player.id,
                    telegram_user_id=player.telegram_user_id,
                    username=player.username,
                    first_name=player.first_name,
                    private_chat_id=player.private_chat_id,
                    balance_dub=player.balance_dub + amount,
                    shield_count=player.shield_count,
                    is_active=player.is_active,
                    is_admin=player.is_admin,
                )
                self.players[username] = updated
                return updated
        return None

    async def set_balance(self, telegram_user_id: int, new_balance: int, reason: str) -> Player | None:
        del reason
        for username, player in self.players.items():
            if player.telegram_user_id == telegram_user_id:
                updated = Player(
                    id=player.id,
                    telegram_user_id=player.telegram_user_id,
                    username=player.username,
                    first_name=player.first_name,
                    private_chat_id=player.private_chat_id,
                    balance_dub=new_balance,
                    shield_count=player.shield_count,
                    is_active=player.is_active,
                    is_admin=player.is_admin,
                )
                self.players[username] = updated
                return updated
        return None


@pytest.mark.asyncio
async def test_admin_give_updates_balance() -> None:
    repo = InMemoryPlayerRepo(
        players={
            "ivan": Player(1, 100, "ivan", "Ivan", 10, 1000, 0, True, False),
        }
    )
    service = AdminCommandService(
        admin_user_ids={1},
        offer_scheduler_service=StubOfferScheduler(),
        settlement_service=StubSettlement(),
        timezone_name="Europe/Moscow",
        player_repo=repo,
        quest_catalog_service=StubQuestCatalog(),
    )

    text = await service.admin_give(requester_user_id=1, target_username="ivan", amount=300, reason="bonus")

    assert "Баланс @ivan: 1300 DUB" in text


@pytest.mark.asyncio
async def test_admin_set_balance_denied_for_non_admin() -> None:
    repo = InMemoryPlayerRepo(players={})
    service = AdminCommandService(
        admin_user_ids={1},
        offer_scheduler_service=StubOfferScheduler(),
        settlement_service=StubSettlement(),
        timezone_name="Europe/Moscow",
        player_repo=repo,
        quest_catalog_service=StubQuestCatalog(),
    )

    text = await service.admin_set_balance(requester_user_id=2, target_username="ivan", amount=500)

    assert "Недостаточно прав" in text
