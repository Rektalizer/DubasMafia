from datetime import datetime

from bot.domain.scheduling import GameScheduleConfig, GameSchedulePolicy, RoundWindow


class ScheduleService:
    def __init__(self, config: GameScheduleConfig) -> None:
        self._config = config
        self._policy = GameSchedulePolicy()

    def current_window(self, now: datetime, test_round_anchor: datetime | None = None) -> RoundWindow:
        return self._policy.current_round_window(
            now=now,
            config=self._config,
            test_round_anchor=test_round_anchor,
        )
