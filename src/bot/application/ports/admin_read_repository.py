from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class DailyQuestStats:
    active_quests: int
    selected_quests: int
    revealed_quests: int


@dataclass(frozen=True, slots=True)
class AdminLogEvent:
    timestamp: datetime
    message: str


class AdminReadRepository(Protocol):
    async def count_players(self) -> int:
        ...

    async def count_players_with_private_chat(self) -> int:
        ...

    async def get_daily_quest_stats(self, quest_date) -> DailyQuestStats:  # type: ignore[no-untyped-def]
        ...

    async def count_messages_between(self, start_at: datetime, end_at: datetime) -> int:
        ...

    async def get_jackpot_total_for_date(self, quest_date) -> int:  # type: ignore[no-untyped-def]
        ...

    async def list_recent_events(self, limit: int) -> list[AdminLogEvent]:
        ...
