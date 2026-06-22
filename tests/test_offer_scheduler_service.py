from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from bot.application.services.daily_quest_service import DailyQuestService
from bot.application.services.offer_scheduler_service import OfferSchedulerService
from bot.application.services.schedule_service import ScheduleService
from bot.domain.player import Player
from bot.domain.quest import DailyQuestOffer, QuestDifficulty, QuestTemplate, QuestValidationRule
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
        return None

    async def set_revealed(self, player_telegram_user_id: int, quest_date: date) -> DailyQuestOffer | None:
        return None


@dataclass
class InMemoryPlayerRepo:
    players: list[Player]

    async def list_active_with_private_chat(self) -> list[Player]:
        return self.players


@dataclass
class StubQuestCatalog:
    templates: list[QuestTemplate]

    def load_enabled(self) -> list[QuestTemplate]:
        return self.templates


@pytest.mark.asyncio
async def test_scheduler_sends_offer_once_per_round() -> None:
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
    daily_repo = InMemoryDailyQuestRepo(offers={})
    daily_service = DailyQuestService(repo=daily_repo)
    player_repo = InMemoryPlayerRepo(
        players=[
            Player(
                id=1,
                telegram_user_id=100,
                username="ivan",
                first_name="Ivan",
                private_chat_id=5000,
                balance_dub=1000,
                shield_count=0,
                is_active=True,
                is_admin=False,
            )
        ]
    )
    catalog = StubQuestCatalog(
        templates=[
            QuestTemplate(
                quest_id="e1",
                difficulty=QuestDifficulty.EASY,
                base_reward=100,
                base_penalty=50,
                requires_target=False,
                target_type="none",
                title="easy",
                description_template="easy quest",
                public_solution="easy",
                validation_rule=QuestValidationRule(
                    validation_type="message_contains_text",
                    must_be_reply=False,
                    text_contains_any=["easy"],
                    target_required=False,
                ),
                ai_validation_enabled=False,
            ),
            QuestTemplate(
                quest_id="m1",
                difficulty=QuestDifficulty.MEDIUM,
                base_reward=250,
                base_penalty=100,
                requires_target=False,
                target_type="none",
                title="medium",
                description_template="medium quest",
                public_solution="medium",
                validation_rule=QuestValidationRule(
                    validation_type="message_contains_text",
                    must_be_reply=False,
                    text_contains_any=["medium"],
                    target_required=False,
                ),
                ai_validation_enabled=False,
            ),
            QuestTemplate(
                quest_id="h1",
                difficulty=QuestDifficulty.HARD,
                base_reward=600,
                base_penalty=250,
                requires_target=False,
                target_type="none",
                title="hard",
                description_template="hard quest",
                public_solution="hard",
                validation_rule=QuestValidationRule(
                    validation_type="custom_ai_check",
                    must_be_reply=False,
                    text_contains_any=[],
                    target_required=False,
                ),
                ai_validation_enabled=True,
            ),
        ]
    )
    sent_to: list[int] = []

    async def sender(player: Player, offer: DailyQuestOffer) -> None:
        del offer
        sent_to.append(player.telegram_user_id)

    service = OfferSchedulerService(
        schedule_service=schedule,
        daily_quest_service=daily_service,
        player_repo=player_repo,
        quest_catalog_service=catalog,
        test_round_anchor=datetime(2026, 6, 22, 10, 0, tzinfo=tz),
    )

    await service.tick(now=datetime(2026, 6, 22, 10, 5, tzinfo=tz), offer_sender=sender)
    await service.tick(now=datetime(2026, 6, 22, 10, 6, tzinfo=tz), offer_sender=sender)

    assert sent_to == [100]
