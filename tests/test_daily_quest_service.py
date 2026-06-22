from dataclasses import dataclass, replace
from datetime import date

import pytest

from bot.application.services.daily_quest_service import DailyQuestService
from bot.domain.quest import DailyQuestOffer, DailyQuestOption, QuestDifficulty, QuestTemplate, QuestValidationRule


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
        offer = self.offers.get((player_telegram_user_id, quest_date))
        if offer is None:
            return None
        selected_option = next(
            option for option in offer.options if option.difficulty == selected_difficulty
        )
        updated = replace(
            offer,
            selected_difficulty=selected_difficulty,
            selected_quest_id=selected_option.quest_id,
            status="accepted",
        )
        self.offers[(player_telegram_user_id, quest_date)] = updated
        return updated

    async def set_revealed(self, player_telegram_user_id: int, quest_date: date) -> DailyQuestOffer | None:
        offer = self.offers.get((player_telegram_user_id, quest_date))
        if offer is None:
            return None
        updated = replace(offer, status="revealed")
        self.offers[(player_telegram_user_id, quest_date)] = updated
        return updated


@pytest.mark.asyncio
async def test_offer_contains_three_difficulties() -> None:
    quests = [
        QuestTemplate(
            quest_id="e1",
            difficulty=QuestDifficulty.EASY,
            base_reward=100,
            base_penalty=50,
            requires_target=False,
            target_type="none",
            title="easy",
            description_template="d",
            public_solution="p",
            validation_rule=QuestValidationRule(
                validation_type="message_contains_text",
                must_be_reply=False,
                text_contains_any=["x"],
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
            description_template="d",
            public_solution="p",
            validation_rule=QuestValidationRule(
                validation_type="reply_contains_text",
                must_be_reply=True,
                text_contains_any=["x"],
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
            description_template="d",
            public_solution="p",
            validation_rule=QuestValidationRule(
                validation_type="custom_ai_check",
                must_be_reply=False,
                text_contains_any=[],
                target_required=False,
            ),
            ai_validation_enabled=True,
        ),
    ]
    repo = InMemoryDailyQuestRepo(offers={})
    service = DailyQuestService(repo=repo)

    offer = await service.create_offer_for_player(
        player_telegram_user_id=100,
        quest_date=date(2026, 6, 22),
        quest_templates=quests,
    )

    assert len(offer.options) == 3
    assert {option.difficulty for option in offer.options} == {
        QuestDifficulty.EASY,
        QuestDifficulty.MEDIUM,
        QuestDifficulty.HARD,
    }


@pytest.mark.asyncio
async def test_accept_offer_returns_none_if_already_accepted() -> None:
    repo = InMemoryDailyQuestRepo(offers={})
    service = DailyQuestService(repo=repo)
    offered = DailyQuestOffer(
        player_telegram_user_id=100,
        quest_date=date(2026, 6, 22),
        options=[
            DailyQuestOption(
                quest_id="e1",
                difficulty=QuestDifficulty.EASY,
                base_reward=100,
                base_penalty=50,
                description_for_player="easy",
                public_solution="easy",
                validation_rule=QuestValidationRule(
                    validation_type="message_contains_text",
                    must_be_reply=False,
                    text_contains_any=["easy"],
                    target_required=False,
                ),
                ai_validation_enabled=False,
                target_user_id=None,
            ),
            DailyQuestOption(
                quest_id="m1",
                difficulty=QuestDifficulty.MEDIUM,
                base_reward=250,
                base_penalty=100,
                description_for_player="medium",
                public_solution="medium",
                validation_rule=QuestValidationRule(
                    validation_type="message_contains_text",
                    must_be_reply=False,
                    text_contains_any=["medium"],
                    target_required=False,
                ),
                ai_validation_enabled=False,
                target_user_id=None,
            ),
            DailyQuestOption(
                quest_id="h1",
                difficulty=QuestDifficulty.HARD,
                base_reward=600,
                base_penalty=250,
                description_for_player="hard",
                public_solution="hard",
                validation_rule=QuestValidationRule(
                    validation_type="message_contains_text",
                    must_be_reply=False,
                    text_contains_any=["hard"],
                    target_required=False,
                ),
                ai_validation_enabled=False,
                target_user_id=None,
            ),
        ],
        selected_difficulty=QuestDifficulty.EASY,
        selected_quest_id="e1",
        status="accepted",
    )
    await repo.save_offer(offered)

    accepted = await service.accept_offer(
        player_telegram_user_id=100,
        quest_date=date(2026, 6, 22),
        selected_difficulty=QuestDifficulty.MEDIUM,
    )

    assert accepted is None
