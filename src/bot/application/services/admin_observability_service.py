from datetime import datetime
from zoneinfo import ZoneInfo

from bot.application.ports.admin_read_repository import AdminReadRepository
from bot.application.services.schedule_service import ScheduleService


class AdminObservabilityService:
    def __init__(
        self,
        admin_user_ids: set[int],
        schedule_service: ScheduleService,
        admin_read_repo: AdminReadRepository,
        timezone_name: str,
        test_round_anchor: datetime | None,
    ) -> None:
        self._admin_user_ids = admin_user_ids
        self._schedule_service = schedule_service
        self._admin_read_repo = admin_read_repo
        self._timezone = ZoneInfo(timezone_name)
        self._test_round_anchor = test_round_anchor

    def _is_admin(self, user_id: int) -> bool:
        return user_id in self._admin_user_ids

    async def admin_status(self, requester_user_id: int) -> str:
        if not self._is_admin(requester_user_id):
            return "Недостаточно прав для админ-команды."

        now = datetime.now(self._timezone)
        window = self._schedule_service.current_window(
            now=now,
            test_round_anchor=self._test_round_anchor,
        )
        players_total = await self._admin_read_repo.count_players()
        players_with_dm = await self._admin_read_repo.count_players_with_private_chat()
        quest_stats = await self._admin_read_repo.get_daily_quest_stats(window.offer_at.date())
        messages_today = await self._admin_read_repo.count_messages_between(
            start_at=window.offer_at,
            end_at=now,
        )
        jackpot_total = await self._admin_read_repo.get_jackpot_total_for_date(window.offer_at.date())

        return (
            "🛠 Admin status\n"
            "Бот: online\n"
            f"Игроков всего: {players_total}\n"
            f"Игроков с личкой: {players_with_dm}\n"
            f"Активных квестов сегодня: {quest_stats.active_quests}\n"
            f"Выбрали квест: {quest_stats.selected_quests}\n"
            f"Уже раскрыто: {quest_stats.revealed_quests}\n"
            f"Сообщений сохранено в раунде: {messages_today}\n"
            f"Jackpot текущий: {jackpot_total} DUB\n"
            f"Следующая проверка: {window.check_at.isoformat()}"
        )

    async def admin_logs(self, requester_user_id: int, limit: int = 10) -> str:
        if not self._is_admin(requester_user_id):
            return "Недостаточно прав для админ-команды."
        events = await self._admin_read_repo.list_recent_events(limit=limit)
        if not events:
            return "Логи пока пустые."
        lines = ["📜 Последние события:"]
        for event in events:
            lines.append(f"{event.timestamp.isoformat()} — {event.message}")
        return "\n".join(lines)
