from datetime import datetime
from zoneinfo import ZoneInfo

from bot.application.services.schedule_service import ScheduleService
from bot.domain.scheduling import GameMode, GameScheduleConfig


def test_schedule_service_returns_window_for_config() -> None:
    cfg = GameScheduleConfig(
        mode=GameMode.TEST,
        timezone="Europe/Moscow",
        offer_hour=8,
        offer_minute=0,
        check_hour=20,
        check_minute=0,
        test_round_duration_minutes=10,
    )
    service = ScheduleService(config=cfg)
    now = datetime(2026, 6, 22, 13, 45, tzinfo=ZoneInfo("Europe/Moscow"))

    window = service.current_window(now=now)

    assert window.offer_at == now
