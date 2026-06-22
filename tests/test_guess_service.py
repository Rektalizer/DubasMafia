from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from bot.application.services.guess_service import GuessService
from bot.application.ports.semantic_evaluator import SemanticEvaluation
from bot.application.services.schedule_service import ScheduleService
from bot.domain.player import Player
from bot.domain.quest import DailyQuestOffer, DailyQuestOption, QuestDifficulty, QuestValidationRule
from bot.domain.scheduling import GameMode, GameScheduleConfig


@dataclass
class InMemoryPlayerRepo:
    players_by_id: dict[int, Player]

    async def get_by_telegram_user_id(self, telegram_user_id: int) -> Player | None:
        return self.players_by_id.get(telegram_user_id)

    async def get_by_username(self, username: str) -> Player | None:
        for player in self.players_by_id.values():
            if player.username == username:
                return player
        return None

    async def create(self, telegram_user_id: int, username: str | None, first_name: str | None, starting_balance: int) -> Player:
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


@dataclass
class InMemoryDailyQuestRepo:
    offers: dict[tuple[int, date], DailyQuestOffer]

    async def save_offer(self, offer: DailyQuestOffer) -> None:
        self.offers[(offer.player_telegram_user_id, offer.quest_date)] = offer

    async def get_offer(self, player_telegram_user_id: int, quest_date: date) -> DailyQuestOffer | None:
        return self.offers.get((player_telegram_user_id, quest_date))

    async def set_selected(self, player_telegram_user_id: int, quest_date: date, selected_difficulty: QuestDifficulty) -> DailyQuestOffer | None:
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
        del player_telegram_user_id, quest_date, status
        return None


class StubSemanticEvaluator:
    async def evaluate_guess(self, public_solution: str, guess_text: str) -> SemanticEvaluation:
        del public_solution, guess_text
        return SemanticEvaluation(matched=True, confidence=0.9, reason="stub")

    async def evaluate_quest_completion(self, description_for_player, public_solution, actor_messages, target_messages):
        del description_for_player, public_solution, actor_messages, target_messages
        return SemanticEvaluation(matched=False, confidence=0.1, reason="unused")


@pytest.mark.asyncio
async def test_guess_reveals_quest_when_solution_matches() -> None:
    tz = ZoneInfo("Europe/Moscow")
    schedule = ScheduleService(
        config=GameScheduleConfig(
            mode=GameMode.PRODUCTION,
            timezone="Europe/Moscow",
            offer_hour=8,
            offer_minute=0,
            check_hour=20,
            check_minute=0,
            test_round_duration_minutes=10,
        )
    )
    players = InMemoryPlayerRepo(
        players_by_id={
            1: Player(1, 1, "guesser", "G", 101, 1000, 0, True, False),
            2: Player(2, 2, "target", "T", 102, 1000, 0, True, False),
        }
    )
    offers = InMemoryDailyQuestRepo(
        offers={
            (2, date(2026, 6, 22)): DailyQuestOffer(
                player_telegram_user_id=2,
                quest_date=date(2026, 6, 22),
                options=[
                    DailyQuestOption(
                        quest_id="q1",
                        difficulty=QuestDifficulty.EASY,
                        base_reward=100,
                        base_penalty=50,
                        description_for_player="desc",
                        public_solution="должен написать слово пельмени",
                        validation_rule=QuestValidationRule(
                            validation_type="custom_ai_check",
                            must_be_reply=False,
                            text_contains_any=[],
                            target_required=False,
                        ),
                        ai_validation_enabled=True,
                        target_user_id=None,
                    )
                ],
                selected_difficulty=QuestDifficulty.EASY,
                selected_quest_id="q1",
                status="accepted",
            )
        }
    )
    service = GuessService(
        player_repo=players,
        daily_quest_repo=offers,
        schedule_service=schedule,
        semantic_evaluator=StubSemanticEvaluator(),
        guess_confidence_threshold=0.75,
        test_round_anchor=None,
    )

    text = await service.process_guess(
        guesser_telegram_user_id=1,
        target_username="target",
        guess_text="он должен написать пельмени",
        now=datetime(2026, 6, 22, 12, 0, tzinfo=tz),
    )

    assert "раскрыл квест" in text
