from datetime import datetime
import logging

from bot.application.ports.daily_quest_repository import DailyQuestRepository
from bot.application.ports.player_repository import PlayerRepository
from bot.application.ports.semantic_evaluator import SemanticEvaluator
from bot.application.services.schedule_service import ScheduleService
from bot.domain.player import Player

logger = logging.getLogger(__name__)


class GuessService:
    def __init__(
        self,
        player_repo: PlayerRepository,
        daily_quest_repo: DailyQuestRepository,
        schedule_service: ScheduleService,
        semantic_evaluator: SemanticEvaluator,
        guess_confidence_threshold: float,
        test_round_anchor: datetime | None,
    ) -> None:
        self._player_repo = player_repo
        self._daily_quest_repo = daily_quest_repo
        self._schedule_service = schedule_service
        self._semantic_evaluator = semantic_evaluator
        self._guess_confidence_threshold = guess_confidence_threshold
        self._test_round_anchor = test_round_anchor

    async def process_guess(
        self,
        guesser_telegram_user_id: int,
        target_username: str,
        guess_text: str,
        now: datetime,
    ) -> str:
        guesser = await self._player_repo.get_by_telegram_user_id(guesser_telegram_user_id)
        if guesser is None:
            return "Сначала подключись к игре через /join."

        target = await self._resolve_target_player(target_username=target_username)
        if target is None:
            return "Этот игрок не участвует в игре."
        if target.telegram_user_id == guesser.telegram_user_id:
            return "Нельзя угадывать свой квест."

        window = self._schedule_service.current_window(
            now=now,
            test_round_anchor=self._test_round_anchor,
        )
        if now >= window.check_at:
            return "Сегодняшняя охота уже закончилась."

        offer = await self._daily_quest_repo.get_offer(
            player_telegram_user_id=target.telegram_user_id,
            quest_date=window.offer_at.date(),
        )
        if offer is None or offer.status == "offered":
            return "Этот игрок ещё не принял секретный квест. Пока угадывать нечего."
        if offer.status == "revealed":
            return "Этот квест уже раскрыт."
        if offer.status != "accepted" or offer.selected_quest_id is None:
            return "Сейчас этот квест недоступен для угадывания."

        selected_option = next(
            (item for item in offer.options if item.quest_id == offer.selected_quest_id),
            None,
        )
        if selected_option is None:
            return "Сейчас этот квест недоступен для угадывания."

        evaluation = await self._semantic_evaluator.evaluate_guess(
            public_solution=selected_option.public_solution,
            guess_text=guess_text,
        )
        logger.info(
            "Guess evaluation: guesser=%s target=%s matched=%s confidence=%.3f threshold=%.3f reason=%s",
            guesser.telegram_user_id,
            target.telegram_user_id,
            evaluation.matched,
            evaluation.confidence,
            self._guess_confidence_threshold,
            evaluation.reason,
        )
        guessed = evaluation.matched and evaluation.confidence >= self._guess_confidence_threshold
        if not guessed:
            return f"Не похоже. Квест @{target.username or target.telegram_user_id} пока не раскрыт."

        await self._daily_quest_repo.set_revealed(
            player_telegram_user_id=target.telegram_user_id,
            quest_date=window.offer_at.date(),
        )
        reveal_reward = selected_option.base_reward
        await self._player_repo.apply_balance_change(
            telegram_user_id=guesser.telegram_user_id,
            amount=reveal_reward,
            reason="guess_reveal_reward",
        )
        return (
            f"🕵️ @{guesser.username or guesser.telegram_user_id} раскрыл квест "
            f"@{target.username or target.telegram_user_id} и забирает {reveal_reward} DUB!"
        )

    async def _resolve_target_player(self, target_username: str) -> Player | None:
        if target_username.isdigit():
            return await self._player_repo.get_by_telegram_user_id(int(target_username))
        return await self._player_repo.get_by_username(target_username)
