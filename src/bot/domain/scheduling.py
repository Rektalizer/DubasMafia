from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from zoneinfo import ZoneInfo


class GameMode(StrEnum):
    PRODUCTION = "production"
    TEST = "test"


@dataclass(frozen=True, slots=True)
class GameScheduleConfig:
    mode: GameMode
    timezone: str
    offer_hour: int
    offer_minute: int
    check_hour: int
    check_minute: int
    test_round_duration_minutes: int


@dataclass(frozen=True, slots=True)
class RoundWindow:
    offer_at: datetime
    check_at: datetime


class GameSchedulePolicy:
    def current_round_window(
        self,
        now: datetime,
        config: GameScheduleConfig,
        test_round_anchor: datetime | None = None,
    ) -> RoundWindow:
        tz_now = self._ensure_timezone(now=now, timezone_name=config.timezone)
        if config.mode == GameMode.TEST:
            if config.test_round_duration_minutes <= 0:
                msg = "test_round_duration_minutes must be positive"
                raise ValueError(msg)
            offer_at = (
                self._ensure_timezone(now=test_round_anchor, timezone_name=config.timezone)
                if test_round_anchor is not None
                else tz_now
            )
            return RoundWindow(
                offer_at=offer_at,
                check_at=offer_at + timedelta(minutes=config.test_round_duration_minutes),
            )

        offer_at = tz_now.replace(
            hour=config.offer_hour,
            minute=config.offer_minute,
            second=0,
            microsecond=0,
        )
        check_at = tz_now.replace(
            hour=config.check_hour,
            minute=config.check_minute,
            second=0,
            microsecond=0,
        )
        if check_at <= offer_at:
            check_at += timedelta(days=1)
        if tz_now < offer_at:
            offer_at -= timedelta(days=1)
            check_at -= timedelta(days=1)
        return RoundWindow(offer_at=offer_at, check_at=check_at)

    def _ensure_timezone(self, now: datetime, timezone_name: str) -> datetime:
        timezone = ZoneInfo(timezone_name)
        if now.tzinfo is None:
            return now.replace(tzinfo=timezone)
        return now.astimezone(timezone)
