from datetime import datetime

from bot.application.services.schedule_service import ScheduleService
from bot.domain.scheduling import GameScheduleConfig


class SystemService:
    def __init__(self, schedule_config: GameScheduleConfig) -> None:
        self._schedule_service = ScheduleService(config=schedule_config)
        self._mode = schedule_config.mode

    def status_text(self, now: datetime, test_round_anchor: datetime | None = None) -> str:
        window = self._schedule_service.current_window(now=now, test_round_anchor=test_round_anchor)
        return (
            f"mode={self._mode.value}; "
            f"offer_at={window.offer_at.isoformat()}; "
            f"check_at={window.check_at.isoformat()}"
        )

    def time_left_text(self, now: datetime, test_round_anchor: datetime | None = None) -> str:
        window = self._schedule_service.current_window(now=now, test_round_anchor=test_round_anchor)
        if now >= window.check_at:
            return (
                "Текущий раунд уже завершён.\n"
                f"Окно раунда: {window.offer_at.isoformat()} -> {window.check_at.isoformat()}"
            )
        remaining = window.check_at - now
        seconds = int(remaining.total_seconds())
        minutes, sec = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        return (
            f"До конца текущего раунда: {hours:02d}:{minutes:02d}:{sec:02d}\n"
            f"Проверка в: {window.check_at.isoformat()}"
        )
