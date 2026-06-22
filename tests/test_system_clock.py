from bot.infrastructure.clock import SystemClock


def test_system_clock_returns_aware_datetime() -> None:
    clock = SystemClock()
    now = clock.now_utc()
    assert now.tzinfo is not None
