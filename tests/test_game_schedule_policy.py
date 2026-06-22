from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from bot.domain.scheduling import (
    GameMode,
    GameScheduleConfig,
    GameSchedulePolicy,
)


def test_production_mode_uses_fixed_offer_and_check_hours() -> None:
    policy = GameSchedulePolicy()
    cfg = GameScheduleConfig(
        mode=GameMode.PRODUCTION,
        timezone="Europe/Moscow",
        offer_hour=8,
        offer_minute=0,
        check_hour=20,
        check_minute=0,
        test_round_duration_minutes=10,
    )
    now = datetime(2026, 6, 22, 9, 30, tzinfo=ZoneInfo("Europe/Moscow"))

    window = policy.current_round_window(now=now, config=cfg)

    assert window.offer_at.hour == 8
    assert window.offer_at.minute == 0
    assert window.check_at.hour == 20
    assert window.check_at.minute == 0


def test_test_mode_runs_short_round_from_start_time() -> None:
    policy = GameSchedulePolicy()
    cfg = GameScheduleConfig(
        mode=GameMode.TEST,
        timezone="Europe/Moscow",
        offer_hour=8,
        offer_minute=0,
        check_hour=20,
        check_minute=0,
        test_round_duration_minutes=10,
    )
    now = datetime(2026, 6, 22, 12, 0, tzinfo=ZoneInfo("Europe/Moscow"))

    window = policy.current_round_window(now=now, config=cfg)

    assert window.offer_at == now
    assert int((window.check_at - window.offer_at).total_seconds()) == 10 * 60


def test_test_mode_requires_positive_duration() -> None:
    policy = GameSchedulePolicy()
    cfg = GameScheduleConfig(
        mode=GameMode.TEST,
        timezone="Europe/Moscow",
        offer_hour=8,
        offer_minute=0,
        check_hour=20,
        check_minute=0,
        test_round_duration_minutes=0,
    )
    now = datetime(2026, 6, 22, 12, 0, tzinfo=ZoneInfo("Europe/Moscow"))

    with pytest.raises(ValueError):
        policy.current_round_window(now=now, config=cfg)
