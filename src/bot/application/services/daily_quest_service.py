from datetime import date
from random import choice

from bot.application.ports.daily_quest_repository import DailyQuestRepository
from bot.domain.quest import DailyQuestOffer, DailyQuestOption, QuestDifficulty, QuestTemplate


class DailyQuestService:
    def __init__(self, repo: DailyQuestRepository) -> None:
        self._repo = repo

    async def create_offer_for_player(
        self,
        player_telegram_user_id: int,
        quest_date: date,
        quest_templates: list[QuestTemplate],
    ) -> DailyQuestOffer:
        by_difficulty: dict[QuestDifficulty, list[QuestTemplate]] = {
            QuestDifficulty.EASY: [],
            QuestDifficulty.MEDIUM: [],
            QuestDifficulty.HARD: [],
        }
        for quest in quest_templates:
            by_difficulty[quest.difficulty].append(quest)

        options: list[DailyQuestOption] = []
        for difficulty in [QuestDifficulty.EASY, QuestDifficulty.MEDIUM, QuestDifficulty.HARD]:
            pool = by_difficulty[difficulty]
            if not pool:
                msg = f"No quests configured for difficulty={difficulty.value}"
                raise ValueError(msg)
            selected = choice(pool)
            options.append(
                DailyQuestOption(
                    quest_id=selected.quest_id,
                    difficulty=selected.difficulty,
                    base_reward=selected.base_reward,
                    base_penalty=selected.base_penalty,
                    description_for_player=selected.description_template,
                    public_solution=selected.public_solution,
                    validation_rule=selected.validation_rule,
                    ai_validation_enabled=selected.ai_validation_enabled,
                    target_user_id=None,
                    hint_text=selected.hint_text,
                )
            )

        offer = DailyQuestOffer(
            player_telegram_user_id=player_telegram_user_id,
            quest_date=quest_date,
            options=options,
            selected_difficulty=None,
            selected_quest_id=None,
            status="offered",
        )
        await self._repo.save_offer(offer=offer)
        return offer

    async def get_offer(
        self,
        player_telegram_user_id: int,
        quest_date: date,
    ) -> DailyQuestOffer | None:
        return await self._repo.get_offer(
            player_telegram_user_id=player_telegram_user_id,
            quest_date=quest_date,
        )

    async def accept_offer(
        self,
        player_telegram_user_id: int,
        quest_date: date,
        selected_difficulty: QuestDifficulty,
    ) -> DailyQuestOffer | None:
        existing = await self._repo.get_offer(
            player_telegram_user_id=player_telegram_user_id,
            quest_date=quest_date,
        )
        if existing is None:
            return None
        if existing.status == "accepted":
            return None
        return await self._repo.set_selected(
            player_telegram_user_id=player_telegram_user_id,
            quest_date=quest_date,
            selected_difficulty=selected_difficulty,
        )
