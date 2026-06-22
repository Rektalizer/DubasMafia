from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from bot.application.ports.admin_read_repository import AdminLogEvent, DailyQuestStats
from bot.application.services.admin_observability_service import AdminObservabilityService
from bot.application.services.schedule_service import ScheduleService
from bot.domain.scheduling import GameMode, GameScheduleConfig


@dataclass
class StubAdminReadRepo:
    async def count_players(self) -> int:
        return 10

    async def count_players_with_private_chat(self) -> int:
        return 7

    async def get_daily_quest_stats(self, quest_date) -> DailyQuestStats:  # type: ignore[no-untyped-def]
        del quest_date
        return DailyQuestStats(active_quests=5, selected_quests=4, revealed_quests=1)

    async def count_messages_between(self, start_at: datetime, end_at: datetime) -> int:
        del start_at, end_at
        return 42

    async def get_jackpot_total_for_date(self, quest_date) -> int:  # type: ignore[no-untyped-def]
        del quest_date
        return 777

    async def list_recent_events(self, limit: int) -> list[AdminLogEvent]:
        del limit
        return [
            AdminLogEvent(
                timestamp=datetime(2026, 6, 22, 12, 0, tzinfo=ZoneInfo("Europe/Moscow")),
                message="event1",
            )
        ]


@pytest.mark.asyncio
async def test_admin_status_denied_for_non_admin() -> None:
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
    service = AdminObservabilityService(
        admin_user_ids={1},
        schedule_service=schedule,
        admin_read_repo=StubAdminReadRepo(),
        timezone_name="Europe/Moscow",
        test_round_anchor=datetime(2026, 6, 22, 10, 0, tzinfo=ZoneInfo("Europe/Moscow")),
    )
    text = await service.admin_status(requester_user_id=2)
    assert "Недостаточно прав" in text


@pytest.mark.asyncio
async def test_admin_logs_returns_events_for_admin() -> None:
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
    service = AdminObservabilityService(
        admin_user_ids={1},
        schedule_service=schedule,
        admin_read_repo=StubAdminReadRepo(),
        timezone_name="Europe/Moscow",
        test_round_anchor=datetime(2026, 6, 22, 10, 0, tzinfo=ZoneInfo("Europe/Moscow")),
    )
    text = await service.admin_logs(requester_user_id=1)
    assert "Последние события" in text
    assert "event1" in text


@pytest.mark.asyncio
async def test_admin_status_shows_jackpot_total() -> None:
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
    service = AdminObservabilityService(
        admin_user_ids={1},
        schedule_service=schedule,
        admin_read_repo=StubAdminReadRepo(),
        timezone_name="Europe/Moscow",
        test_round_anchor=datetime(2026, 6, 22, 10, 0, tzinfo=ZoneInfo("Europe/Moscow")),
    )
    text = await service.admin_status(requester_user_id=1)
    assert "Jackpot текущий: 777 DUB" in text
