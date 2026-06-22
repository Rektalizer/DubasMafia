from datetime import date
from typing import Protocol

from bot.domain.quest import DailyQuestOffer, QuestDifficulty


class DailyQuestRepository(Protocol):
    async def save_offer(self, offer: DailyQuestOffer) -> None:
        ...

    async def get_offer(self, player_telegram_user_id: int, quest_date: date) -> DailyQuestOffer | None:
        ...

    async def set_selected(
        self,
        player_telegram_user_id: int,
        quest_date: date,
        selected_difficulty: QuestDifficulty,
    ) -> DailyQuestOffer | None:
        ...

    async def set_revealed(self, player_telegram_user_id: int, quest_date: date) -> DailyQuestOffer | None:
        ...

    async def list_by_date(self, quest_date: date) -> list[DailyQuestOffer]:
        ...

    async def set_status(
        self,
        player_telegram_user_id: int,
        quest_date: date,
        status: str,
    ) -> DailyQuestOffer | None:
        ...

    async def set_double_active(self, player_telegram_user_id: int, quest_date: date) -> DailyQuestOffer | None:
        ...
