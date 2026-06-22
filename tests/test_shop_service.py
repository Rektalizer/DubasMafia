from dataclasses import dataclass, replace
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from bot.application.services.schedule_service import ScheduleService
from bot.application.services.shop_service import ShopService, ShopSettings
from bot.domain.player import Player
from bot.domain.quest import DailyQuestOffer
from bot.domain.scheduling import GameMode, GameScheduleConfig


@dataclass
class InMemoryPlayerRepo:
    players: dict[int, Player]

    async def get_by_telegram_user_id(self, telegram_user_id: int) -> Player | None:
        return self.players.get(telegram_user_id)

    async def get_by_username(self, username: str) -> Player | None:
        for player in self.players.values():
            if player.username == username:
                return player
        return None

    async def create(self, telegram_user_id, username, first_name, starting_balance):  # type: ignore[no-untyped-def]
        del telegram_user_id, username, first_name, starting_balance
        raise NotImplementedError

    async def update_private_chat_id(self, telegram_user_id: int, private_chat_id: int) -> None:
        del telegram_user_id, private_chat_id
        raise NotImplementedError

    async def top_by_balance(self, limit: int) -> list[Player]:
        del limit
        return []

    async def list_active_with_private_chat(self) -> list[Player]:
        return []

    async def apply_balance_change(self, telegram_user_id: int, amount: int, reason: str) -> Player | None:
        del reason
        player = self.players.get(telegram_user_id)
        if player is None:
            return None
        updated = replace(player, balance_dub=player.balance_dub + amount)
        self.players[telegram_user_id] = updated
        return updated

    async def set_balance(self, telegram_user_id: int, new_balance: int, reason: str) -> Player | None:
        del reason
        player = self.players.get(telegram_user_id)
        if player is None:
            return None
        updated = replace(player, balance_dub=new_balance)
        self.players[telegram_user_id] = updated
        return updated

    async def add_shield(self, telegram_user_id: int, delta: int) -> Player | None:
        player = self.players.get(telegram_user_id)
        if player is None:
            return None
        updated = replace(player, shield_count=player.shield_count + delta)
        self.players[telegram_user_id] = updated
        return updated


@dataclass
class InMemoryDailyRepo:
    offers: dict[tuple[int, date], DailyQuestOffer]

    async def get_offer(self, player_telegram_user_id: int, quest_date: date) -> DailyQuestOffer | None:
        return self.offers.get((player_telegram_user_id, quest_date))

    async def set_double_active(self, player_telegram_user_id: int, quest_date: date) -> DailyQuestOffer | None:
        offer = self.offers.get((player_telegram_user_id, quest_date))
        if offer is None:
            return None
        updated = replace(offer, double_active=True)
        self.offers[(player_telegram_user_id, quest_date)] = updated
        return updated

    async def save_offer(self, offer: DailyQuestOffer) -> None:
        self.offers[(offer.player_telegram_user_id, offer.quest_date)] = offer


@dataclass
class InMemoryJackpotRepo:
    contributions: dict[tuple[date, int], int]
    carryover: int = 0

    async def get_contribution(self, quest_date: date, telegram_user_id: int) -> int:
        return self.contributions.get((quest_date, telegram_user_id), 0)

    async def add_contribution(self, quest_date: date, telegram_user_id: int, amount: int) -> int:
        key = (quest_date, telegram_user_id)
        current = self.contributions.get(key, 0)
        self.contributions[key] = current + amount
        return self.contributions[key]

    async def get_total_for_date(self, quest_date: date) -> int:
        total = sum(amount for (d, _), amount in self.contributions.items() if d == quest_date)
        return total + self.carryover

    async def get_carryover(self) -> int:
        return self.carryover

    async def set_carryover(self, amount: int) -> None:
        self.carryover = amount


@dataclass
class InMemoryShopActionRepo:
    actions: list[tuple[str, int | None, datetime]]

    async def get_last_action_at(self, action_type: str, target_telegram_user_id: int) -> datetime | None:
        candidates = [
            created_at
            for kind, target_id, created_at in self.actions
            if kind == action_type and target_id == target_telegram_user_id
        ]
        if not candidates:
            return None
        return max(candidates)

    async def add_action(
        self,
        action_type: str,
        buyer_telegram_user_id: int,
        target_telegram_user_id: int | None,
        result: str,
        created_at: datetime,
    ) -> None:
        del buyer_telegram_user_id, result
        self.actions.append((action_type, target_telegram_user_id, created_at))


@dataclass
class StubDailyQuestService:
    repo: InMemoryDailyRepo

    async def create_offer_for_player(self, player_telegram_user_id: int, quest_date: date, quest_templates):  # type: ignore[no-untyped-def]
        del quest_templates
        existing = await self.repo.get_offer(player_telegram_user_id, quest_date)
        if existing is None:
            return None
        rerolled = replace(existing, status="offered", selected_difficulty=None, selected_quest_id=None)
        await self.repo.save_offer(rerolled)
        return rerolled


@dataclass
class StubQuestCatalog:
    def load_enabled(self):  # type: ignore[no-untyped-def]
        return []


@pytest.mark.asyncio
async def test_buy_shield_deducts_balance_and_adds_shield() -> None:
    schedule = ScheduleService(
        config=GameScheduleConfig(
            mode=GameMode.TEST,
            timezone="Europe/Moscow",
            offer_hour=8,
            offer_minute=0,
            check_hour=20,
            check_minute=0,
            test_round_duration_minutes=10,
        )
    )
    player_repo = InMemoryPlayerRepo(
        players={100: Player(1, 100, "ivan", "Ivan", 1000, 1000, 0, True, False)}
    )
    service = ShopService(
        player_repo=player_repo,
        daily_quest_repo=InMemoryDailyRepo(offers={}),
        jackpot_repo=InMemoryJackpotRepo(contributions={}),
        daily_quest_service=StubDailyQuestService(repo=InMemoryDailyRepo(offers={})),
        quest_catalog_service=StubQuestCatalog(),
        shop_action_repo=InMemoryShopActionRepo(actions=[]),
        schedule_service=schedule,
        settings=ShopSettings(
            shield_price=700,
            double_price=500,
            reroll_price=150,
            hint_price=300,
            mute_price=1000,
            mute_duration_minutes=5,
            mute_cooldown_minutes=60,
            jackpot_min=50,
            jackpot_max_per_day=500,
        ),
        test_round_anchor=datetime(2026, 6, 22, 10, 0, tzinfo=ZoneInfo("Europe/Moscow")),
    )

    text = await service.buy_shield(telegram_user_id=100)

    assert "Shield куплен" in text
    assert player_repo.players[100].balance_dub == 300
    assert player_repo.players[100].shield_count == 1


@pytest.mark.asyncio
async def test_buy_double_requires_accepted_quest() -> None:
    schedule = ScheduleService(
        config=GameScheduleConfig(
            mode=GameMode.TEST,
            timezone="Europe/Moscow",
            offer_hour=8,
            offer_minute=0,
            check_hour=20,
            check_minute=0,
            test_round_duration_minutes=10,
        )
    )
    player_repo = InMemoryPlayerRepo(
        players={100: Player(1, 100, "ivan", "Ivan", 1000, 1000, 0, True, False)}
    )
    service = ShopService(
        player_repo=player_repo,
        daily_quest_repo=InMemoryDailyRepo(offers={}),
        jackpot_repo=InMemoryJackpotRepo(contributions={}),
        daily_quest_service=StubDailyQuestService(repo=InMemoryDailyRepo(offers={})),
        quest_catalog_service=StubQuestCatalog(),
        shop_action_repo=InMemoryShopActionRepo(actions=[]),
        schedule_service=schedule,
        settings=ShopSettings(
            shield_price=700,
            double_price=500,
            reroll_price=150,
            hint_price=300,
            mute_price=1000,
            mute_duration_minutes=5,
            mute_cooldown_minutes=60,
            jackpot_min=50,
            jackpot_max_per_day=500,
        ),
        test_round_anchor=datetime(2026, 6, 22, 10, 0, tzinfo=ZoneInfo("Europe/Moscow")),
    )

    text = await service.buy_double(telegram_user_id=100, now=datetime(2026, 6, 22, 10, 2, tzinfo=ZoneInfo("Europe/Moscow")))

    assert "сначала прими квест" in text.lower()


@pytest.mark.asyncio
async def test_buy_reroll_replaces_unaccepted_offer() -> None:
    schedule = ScheduleService(
        config=GameScheduleConfig(
            mode=GameMode.TEST,
            timezone="Europe/Moscow",
            offer_hour=8,
            offer_minute=0,
            check_hour=20,
            check_minute=0,
            test_round_duration_minutes=10,
        )
    )
    repo = InMemoryDailyRepo(
        offers={
            (100, date(2026, 6, 22)): DailyQuestOffer(
                player_telegram_user_id=100,
                quest_date=date(2026, 6, 22),
                options=[],
                selected_difficulty=None,
                selected_quest_id=None,
                status="offered",
            )
        }
    )
    player_repo = InMemoryPlayerRepo(
        players={100: Player(1, 100, "ivan", "Ivan", 1000, 1000, 0, True, False)}
    )
    service = ShopService(
        player_repo=player_repo,
        daily_quest_repo=repo,
        jackpot_repo=InMemoryJackpotRepo(contributions={}),
        daily_quest_service=StubDailyQuestService(repo=repo),
        quest_catalog_service=StubQuestCatalog(),
        shop_action_repo=InMemoryShopActionRepo(actions=[]),
        schedule_service=schedule,
        settings=ShopSettings(
            shield_price=700,
            double_price=500,
            reroll_price=150,
            hint_price=300,
            mute_price=1000,
            mute_duration_minutes=5,
            mute_cooldown_minutes=60,
            jackpot_min=50,
            jackpot_max_per_day=500,
        ),
        test_round_anchor=datetime(2026, 6, 22, 10, 0, tzinfo=ZoneInfo("Europe/Moscow")),
    )

    text = await service.buy_reroll(telegram_user_id=100, now=datetime(2026, 6, 22, 10, 3, tzinfo=ZoneInfo("Europe/Moscow")))

    assert "Reroll выполнен" in text
    assert player_repo.players[100].balance_dub == 850


@pytest.mark.asyncio
async def test_buy_hint_for_revealed_quest_denied() -> None:
    schedule = ScheduleService(
        config=GameScheduleConfig(
            mode=GameMode.TEST,
            timezone="Europe/Moscow",
            offer_hour=8,
            offer_minute=0,
            check_hour=20,
            check_minute=0,
            test_round_duration_minutes=10,
        )
    )
    repo = InMemoryDailyRepo(
        offers={
            (200, date(2026, 6, 22)): DailyQuestOffer(
                player_telegram_user_id=200,
                quest_date=date(2026, 6, 22),
                options=[],
                selected_difficulty=None,
                selected_quest_id=None,
                status="revealed",
            )
        }
    )
    players = InMemoryPlayerRepo(
        players={
            100: Player(1, 100, "ivan", "Ivan", 1000, 1000, 0, True, False),
            200: Player(2, 200, "max", "Max", 1001, 1000, 0, True, False),
        }
    )
    service = ShopService(
        player_repo=players,
        daily_quest_repo=repo,
        jackpot_repo=InMemoryJackpotRepo(contributions={}),
        daily_quest_service=StubDailyQuestService(repo=repo),
        quest_catalog_service=StubQuestCatalog(),
        shop_action_repo=InMemoryShopActionRepo(actions=[]),
        schedule_service=schedule,
        settings=ShopSettings(
            shield_price=700,
            double_price=500,
            reroll_price=150,
            hint_price=300,
            mute_price=1000,
            mute_duration_minutes=5,
            mute_cooldown_minutes=60,
            jackpot_min=50,
            jackpot_max_per_day=500,
        ),
        test_round_anchor=datetime(2026, 6, 22, 10, 0, tzinfo=ZoneInfo("Europe/Moscow")),
    )

    text = await service.buy_hint(
        buyer_telegram_user_id=100,
        target_username="max",
        now=datetime(2026, 6, 22, 10, 4, tzinfo=ZoneInfo("Europe/Moscow")),
    )

    assert "уже раскрыт" in text.lower()


@pytest.mark.asyncio
async def test_buy_mute_consumes_shield_without_executor_call() -> None:
    schedule = ScheduleService(
        config=GameScheduleConfig(
            mode=GameMode.TEST,
            timezone="Europe/Moscow",
            offer_hour=8,
            offer_minute=0,
            check_hour=20,
            check_minute=0,
            test_round_duration_minutes=10,
        )
    )
    players = InMemoryPlayerRepo(
        players={
            100: Player(1, 100, "buyer", "Buyer", 1000, 1500, 0, True, False),
            200: Player(2, 200, "target", "Target", 1001, 1000, 1, True, False),
        }
    )
    action_repo = InMemoryShopActionRepo(actions=[])
    service = ShopService(
        player_repo=players,
        daily_quest_repo=InMemoryDailyRepo(offers={}),
        jackpot_repo=InMemoryJackpotRepo(contributions={}),
        daily_quest_service=StubDailyQuestService(repo=InMemoryDailyRepo(offers={})),
        quest_catalog_service=StubQuestCatalog(),
        shop_action_repo=action_repo,
        schedule_service=schedule,
        settings=ShopSettings(
            shield_price=700,
            double_price=500,
            reroll_price=150,
            hint_price=300,
            mute_price=1000,
            mute_duration_minutes=5,
            mute_cooldown_minutes=60,
            jackpot_min=50,
            jackpot_max_per_day=500,
        ),
        test_round_anchor=datetime(2026, 6, 22, 10, 0, tzinfo=ZoneInfo("Europe/Moscow")),
    )
    called = {"value": False}

    async def mute_executor(chat_id: int, target_user_id: int, duration_minutes: int) -> bool:
        del chat_id, target_user_id, duration_minutes
        called["value"] = True
        return True

    text = await service.buy_mute(
        buyer_telegram_user_id=100,
        target_username="target",
        now=datetime(2026, 6, 22, 10, 5, tzinfo=ZoneInfo("Europe/Moscow")),
        group_chat_id=-100,
        bot_telegram_user_id=999,
        admin_user_ids=set(),
        mute_executor=mute_executor,
    )

    assert "щит спас" in text.lower()
    assert called["value"] is False
    assert players.players[100].balance_dub == 500
    assert players.players[200].shield_count == 0


@pytest.mark.asyncio
async def test_buy_mute_no_rights_does_not_charge() -> None:
    schedule = ScheduleService(
        config=GameScheduleConfig(
            mode=GameMode.TEST,
            timezone="Europe/Moscow",
            offer_hour=8,
            offer_minute=0,
            check_hour=20,
            check_minute=0,
            test_round_duration_minutes=10,
        )
    )
    players = InMemoryPlayerRepo(
        players={
            100: Player(1, 100, "buyer", "Buyer", 1000, 1500, 0, True, False),
            200: Player(2, 200, "target", "Target", 1001, 1000, 0, True, False),
        }
    )
    service = ShopService(
        player_repo=players,
        daily_quest_repo=InMemoryDailyRepo(offers={}),
        jackpot_repo=InMemoryJackpotRepo(contributions={}),
        daily_quest_service=StubDailyQuestService(repo=InMemoryDailyRepo(offers={})),
        quest_catalog_service=StubQuestCatalog(),
        shop_action_repo=InMemoryShopActionRepo(actions=[]),
        schedule_service=schedule,
        settings=ShopSettings(
            shield_price=700,
            double_price=500,
            reroll_price=150,
            hint_price=300,
            mute_price=1000,
            mute_duration_minutes=5,
            mute_cooldown_minutes=60,
            jackpot_min=50,
            jackpot_max_per_day=500,
        ),
        test_round_anchor=datetime(2026, 6, 22, 10, 0, tzinfo=ZoneInfo("Europe/Moscow")),
    )

    async def mute_executor(chat_id: int, target_user_id: int, duration_minutes: int) -> bool:
        del chat_id, target_user_id, duration_minutes
        return False

    text = await service.buy_mute(
        buyer_telegram_user_id=100,
        target_username="target",
        now=datetime(2026, 6, 22, 10, 5, tzinfo=ZoneInfo("Europe/Moscow")),
        group_chat_id=-100,
        bot_telegram_user_id=999,
        admin_user_ids=set(),
        mute_executor=mute_executor,
    )

    assert "нет нужных прав" in text.lower()
    assert players.players[100].balance_dub == 1500
