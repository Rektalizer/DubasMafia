from datetime import datetime

from bot.application.services.schedule_service import ScheduleService
from bot.domain.scheduling import GameScheduleConfig


class SystemService:
    def __init__(self, schedule_config: GameScheduleConfig) -> None:
        self._schedule_service = ScheduleService(config=schedule_config)
        self._mode = schedule_config.mode

    def status_text(self, now: datetime) -> str:
        window = self._schedule_service.current_window(now=now)
        return (
            f"mode={self._mode.value}; "
            f"offer_at={window.offer_at.isoformat()}; "
            f"check_at={window.check_at.isoformat()}"
        )
