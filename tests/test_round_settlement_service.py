from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from bot.application.services.round_settlement_service import RoundSettlementService
from bot.application.services.quest_completion_service import QuestCompletionService
from bot.application.ports.semantic_evaluator import SemanticEvaluation
from bot.application.services.schedule_service import ScheduleService
from bot.domain.chat_message import ChatMessage
from bot.domain.player import Player
from bot.domain.quest import DailyQuestOffer, DailyQuestOption, QuestDifficulty, QuestValidationRule
from bot.domain.scheduling import GameMode, GameScheduleConfig


@dataclass
class InMemoryDailyQuestRepo:
    offers: dict[tuple[int, date], DailyQuestOffer]

    async def save_offer(self, offer: DailyQuestOffer) -> None:
        self.offers[(offer.player_telegram_user_id, offer.quest_date)] = offer

    async def get_offer(self, player_telegram_user_id: int, quest_date: date) -> DailyQuestOffer | None:
        return self.offers.get((player_telegram_user_id, quest_date))

    async def set_selected(
        self,
        player_telegram_user_id: int,
        quest_date: date,
        selected_difficulty: QuestDifficulty,
    ) -> DailyQuestOffer | None:
        del player_telegram_user_id, quest_date, selected_difficulty
        return None

    async def set_revealed(self, player_telegram_user_id: int, quest_date: date) -> DailyQuestOffer | None:
        offer = self.offers.get((player_telegram_user_id, quest_date))
        if offer is None:
            return None
        updated = DailyQuestOffer(
            player_telegram_user_id=offer.player_telegram_user_id,
            quest_date=offer.quest_date,
            options=offer.options,
            selected_difficulty=offer.selected_difficulty,
            selected_quest_id=offer.selected_quest_id,
            status="revealed",
        )
        self.offers[(player_telegram_user_id, quest_date)] = updated
        return updated

    async def list_by_date(self, quest_date: date) -> list[DailyQuestOffer]:
        return [offer for (_, d), offer in self.offers.items() if d == quest_date]

    async def set_status(self, player_telegram_user_id: int, quest_date: date, status: str) -> DailyQuestOffer | None:
        offer = self.offers.get((player_telegram_user_id, quest_date))
        if offer is None:
            return None
        updated = DailyQuestOffer(
            player_telegram_user_id=offer.player_telegram_user_id,
            quest_date=offer.quest_date,
            options=offer.options,
            selected_difficulty=offer.selected_difficulty,
            selected_quest_id=offer.selected_quest_id,
            status=status,
        )
        self.offers[(player_telegram_user_id, quest_date)] = updated
        return updated


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

    async def create(
        self,
        telegram_user_id: int,
        username: str | None,
        first_name: str | None,
        starting_balance: int,
    ) -> Player:
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
        self.players[telegram_user_id] = updated
        return updated


@dataclass
class InMemoryChatMessageRepo:
    messages: list[ChatMessage]

    async def save(self, message: ChatMessage) -> None:
        self.messages.append(message)

    async def has_message_in_window(
        self,
        chat_id: int,
        author_user_id: int,
        start_at: datetime,
        end_at: datetime,
    ) -> bool:
        for message in self.messages:
            if message.chat_id != chat_id:
                continue
            if message.author_user_id != author_user_id:
                continue
            if start_at <= message.created_at < end_at:
                return True
        return False

    async def list_messages_in_window(
        self,
        chat_id: int,
        author_user_id: int,
        start_at: datetime,
        end_at: datetime,
    ) -> list[ChatMessage]:
        return [
            message
            for message in self.messages
            if message.chat_id == chat_id
            and message.author_user_id == author_user_id
            and start_at <= message.created_at < end_at
        ]


@dataclass
class InMemoryJackpotRepo:
    carryover: int = 0
    day_total: int = 0

    async def get_contribution(self, quest_date: date, telegram_user_id: int) -> int:
        del quest_date, telegram_user_id
        return 0

    async def add_contribution(self, quest_date: date, telegram_user_id: int, amount: int) -> int:
        del quest_date, telegram_user_id, amount
        return 0

    async def get_total_for_date(self, quest_date: date) -> int:
        del quest_date
        return self.day_total + self.carryover

    async def get_carryover(self) -> int:
        return self.carryover

    async def set_carryover(self, amount: int) -> None:
        self.carryover = amount


class StubSemanticEvaluator:
    async def evaluate_guess(self, public_solution: str, guess_text: str) -> SemanticEvaluation:
        del public_solution, guess_text
        return SemanticEvaluation(matched=False, confidence=0.1, reason="unused")

    async def evaluate_quest_completion(self, description_for_player, public_solution, actor_messages, target_messages):
        del description_for_player, public_solution, actor_messages, target_messages
        return SemanticEvaluation(matched=False, confidence=0.1, reason="unused")


@pytest.mark.asyncio
async def test_settlement_applies_reward_and_penalty() -> None:
    tz = ZoneInfo("Europe/Moscow")
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
    offer_date = date(2026, 6, 22)
    offer_start = datetime(2026, 6, 22, 10, 0, tzinfo=tz)
    daily_repo = InMemoryDailyQuestRepo(
        offers={
            (100, offer_date): DailyQuestOffer(
                player_telegram_user_id=100,
                quest_date=offer_date,
                options=[
                    DailyQuestOption(
                        quest_id="e1",
                        difficulty=QuestDifficulty.EASY,
                        base_reward=100,
                        base_penalty=50,
                        description_for_player="easy",
                        public_solution="слово",
                        validation_rule=QuestValidationRule(
                            validation_type="message_contains_text",
                            must_be_reply=False,
                            text_contains_any=["hello"],
                            target_required=False,
                        ),
                        ai_validation_enabled=False,
                        target_user_id=None,
                    )
                ],
                selected_difficulty=QuestDifficulty.EASY,
                selected_quest_id="e1",
                status="accepted",
            ),
            (200, offer_date): DailyQuestOffer(
                player_telegram_user_id=200,
                quest_date=offer_date,
                options=[
                    DailyQuestOption(
                        quest_id="m1",
                        difficulty=QuestDifficulty.MEDIUM,
                        base_reward=250,
                        base_penalty=100,
                        description_for_player="medium",
                        public_solution="слово",
                        validation_rule=QuestValidationRule(
                            validation_type="message_contains_text",
                            must_be_reply=False,
                            text_contains_any=["missing"],
                            target_required=False,
                        ),
                        ai_validation_enabled=False,
                        target_user_id=None,
                    )
                ],
                selected_difficulty=QuestDifficulty.MEDIUM,
                selected_quest_id="m1",
                status="accepted",
            ),
        }
    )
    players = InMemoryPlayerRepo(
        players={
            100: Player(1, 100, "one", "One", 101, 1000, 0, True, False),
            200: Player(2, 200, "two", "Two", 102, 1000, 0, True, False),
        }
    )
    messages = InMemoryChatMessageRepo(
        messages=[
            ChatMessage(
                telegram_message_id=1,
                chat_id=-500,
                author_user_id=100,
                author_username="one",
                text="hello",
                replied_message_id=None,
                replied_author_user_id=None,
                created_at=datetime(2026, 6, 22, 10, 4, tzinfo=tz),
            )
        ]
    )
    service = RoundSettlementService(
        schedule_service=schedule,
        daily_quest_repo=daily_repo,
        player_repo=players,
        chat_message_repo=messages,
        jackpot_repo=InMemoryJackpotRepo(),
        quest_completion_service=QuestCompletionService(
            semantic_evaluator=StubSemanticEvaluator(),
            ai_confidence_threshold=0.7,
        ),
        group_chat_id=-500,
        test_round_anchor=offer_start,
    )

    report = await service.settle_if_due(now=datetime(2026, 6, 22, 10, 11, tzinfo=tz))

    assert report is not None
    assert players.players[100].balance_dub == 1100
    assert players.players[200].balance_dub == 900


@pytest.mark.asyncio
async def test_settlement_applies_double_multiplier() -> None:
    tz = ZoneInfo("Europe/Moscow")
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
    offer_date = date(2026, 6, 22)
    daily_repo = InMemoryDailyQuestRepo(
        offers={
            (100, offer_date): DailyQuestOffer(
                player_telegram_user_id=100,
                quest_date=offer_date,
                options=[
                    DailyQuestOption(
                        quest_id="e1",
                        difficulty=QuestDifficulty.EASY,
                        base_reward=100,
                        base_penalty=50,
                        description_for_player="easy",
                        public_solution="слово",
                        validation_rule=QuestValidationRule(
                            validation_type="message_contains_text",
                            must_be_reply=False,
                            text_contains_any=["hello"],
                            target_required=False,
                        ),
                        ai_validation_enabled=False,
                        target_user_id=None,
                    )
                ],
                selected_difficulty=QuestDifficulty.EASY,
                selected_quest_id="e1",
                status="accepted",
                double_active=True,
            ),
        }
    )
    players = InMemoryPlayerRepo(
        players={100: Player(1, 100, "one", "One", 101, 1000, 0, True, False)}
    )
    messages = InMemoryChatMessageRepo(
        messages=[
            ChatMessage(
                telegram_message_id=1,
                chat_id=-500,
                author_user_id=100,
                author_username="one",
                text="hello",
                replied_message_id=None,
                replied_author_user_id=None,
                created_at=datetime(2026, 6, 22, 10, 4, tzinfo=tz),
            )
        ]
    )
    service = RoundSettlementService(
        schedule_service=schedule,
        daily_quest_repo=daily_repo,
        player_repo=players,
        chat_message_repo=messages,
        jackpot_repo=InMemoryJackpotRepo(),
        quest_completion_service=QuestCompletionService(
            semantic_evaluator=StubSemanticEvaluator(),
            ai_confidence_threshold=0.7,
        ),
        group_chat_id=-500,
        test_round_anchor=datetime(2026, 6, 22, 10, 0, tzinfo=tz),
    )

    report = await service.settle_if_due(now=datetime(2026, 6, 22, 10, 11, tzinfo=tz))

    assert report is not None
    assert "+200 DUB" in report
    assert players.players[100].balance_dub == 1200


@pytest.mark.asyncio
async def test_settlement_moves_jackpot_to_carryover_if_no_eligible() -> None:
    tz = ZoneInfo("Europe/Moscow")
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
    offer_date = date(2026, 6, 22)
    daily_repo = InMemoryDailyQuestRepo(
        offers={
            (100, offer_date): DailyQuestOffer(
                player_telegram_user_id=100,
                quest_date=offer_date,
                options=[],
                selected_difficulty=None,
                selected_quest_id=None,
                status="revealed",
            ),
        }
    )
    players = InMemoryPlayerRepo(
        players={100: Player(1, 100, "one", "One", 101, 1000, 0, True, False)}
    )
    messages = InMemoryChatMessageRepo(messages=[])
    jackpot_repo = InMemoryJackpotRepo(day_total=700, carryover=0)
    service = RoundSettlementService(
        schedule_service=schedule,
        daily_quest_repo=daily_repo,
        player_repo=players,
        chat_message_repo=messages,
        jackpot_repo=jackpot_repo,
        quest_completion_service=QuestCompletionService(
            semantic_evaluator=StubSemanticEvaluator(),
            ai_confidence_threshold=0.7,
        ),
        group_chat_id=-500,
        test_round_anchor=datetime(2026, 6, 22, 10, 0, tzinfo=tz),
    )

    report = await service.settle_if_due(now=datetime(2026, 6, 22, 10, 11, tzinfo=tz))

    assert report is not None
    assert "перенесён на следующий день" in report
    assert jackpot_repo.carryover == 700
