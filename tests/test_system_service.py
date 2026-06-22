from datetime import datetime
from zoneinfo import ZoneInfo

from bot.application.services.system_service import SystemService
from bot.domain.scheduling import GameMode, GameScheduleConfig


def test_system_service_reports_mode_and_window() -> None:
    service = SystemService(
        schedule_config=GameScheduleConfig(
            mode=GameMode.TEST,
            timezone="Europe/Moscow",
            offer_hour=8,
            offer_minute=0,
            check_hour=20,
            check_minute=0,
            test_round_duration_minutes=10,
        )
    )
    now = datetime(2026, 6, 22, 10, 15, tzinfo=ZoneInfo("Europe/Moscow"))

    text = service.status_text(now=now)

    assert "mode=test" in text
    assert "offer_at=2026-06-22T10:15:00+03:00" in text


def test_system_service_time_left_uses_test_round_anchor() -> None:
    service = SystemService(
        schedule_config=GameScheduleConfig(
            mode=GameMode.TEST,
            timezone="Europe/Moscow",
            offer_hour=8,
            offer_minute=0,
            check_hour=20,
            check_minute=0,
            test_round_duration_minutes=10,
        )
    )
    tz = ZoneInfo("Europe/Moscow")
    anchor = datetime(2026, 6, 22, 10, 0, tzinfo=tz)
    now = datetime(2026, 6, 22, 10, 5, tzinfo=tz)

    text = service.time_left_text(now=now, test_round_anchor=anchor)

    assert "До конца текущего раунда: 00:05:00" in text
