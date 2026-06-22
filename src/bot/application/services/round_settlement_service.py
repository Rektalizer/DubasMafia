import random
from datetime import datetime

from bot.application.ports.chat_message_repository import ChatMessageRepository
from bot.application.ports.daily_quest_repository import DailyQuestRepository
from bot.application.ports.jackpot_repository import JackpotRepository
from bot.application.ports.player_repository import PlayerRepository
from bot.application.services.quest_completion_service import QuestCompletionService
from bot.application.services.schedule_service import ScheduleService
from bot.domain.quest import DailyQuestOffer


class RoundSettlementService:
    def __init__(
        self,
        schedule_service: ScheduleService,
        daily_quest_repo: DailyQuestRepository,
        player_repo: PlayerRepository,
        chat_message_repo: ChatMessageRepository,
        jackpot_repo: JackpotRepository,
        quest_completion_service: QuestCompletionService,
        group_chat_id: int,
        test_round_anchor: datetime | None,
    ) -> None:
        self._schedule_service = schedule_service
        self._daily_quest_repo = daily_quest_repo
        self._player_repo = player_repo
        self._chat_message_repo = chat_message_repo
        self._jackpot_repo = jackpot_repo
        self._quest_completion_service = quest_completion_service
        self._group_chat_id = group_chat_id
        self._test_round_anchor = test_round_anchor
        self._settled_round_keys: set[str] = set()

    async def settle_if_due(self, now: datetime) -> str | None:
        return await self._settle(
            now=now,
            require_check_time=True,
        )

    async def settle_now(self, now: datetime) -> str | None:
        return await self._settle(
            now=now,
            require_check_time=False,
        )

    async def _settle(self, now: datetime, require_check_time: bool) -> str | None:
        window = self._schedule_service.current_window(
            now=now,
            test_round_anchor=self._test_round_anchor,
        )
        if require_check_time and now < window.check_at:
            return None

        round_key = f"{window.offer_at.isoformat()}::{window.check_at.isoformat()}"
        if round_key in self._settled_round_keys:
            return None

        offers = await self._daily_quest_repo.list_by_date(window.offer_at.date())
        if not offers:
            self._settled_round_keys.add(round_key)
            return "🌙 Итоги тайных квестов\nСегодня активных квестов не было."

        lines = ["🌙 Итоги тайных квестов"]
        eligible_for_jackpot: list[int] = []
        for offer in offers:
            line, eligible_player_id = await self._settle_offer(
                offer=offer,
                start_at=window.offer_at,
                end_at=window.check_at,
            )
            if eligible_player_id is not None:
                eligible_for_jackpot.append(eligible_player_id)
            if line:
                lines.append(line)

        jackpot_line = await self._settle_jackpot(
            quest_date=window.offer_at.date(),
            eligible_player_ids=eligible_for_jackpot,
        )
        if jackpot_line:
            lines.append(jackpot_line)

        if len(lines) == 1:
            lines.append("Сегодня не было квестов для проверки.")

        self._settled_round_keys.add(round_key)
        return "\n".join(lines)

    async def _settle_offer(
        self,
        offer: DailyQuestOffer,
        start_at: datetime,
        end_at: datetime,
    ) -> tuple[str | None, int | None]:
        player = await self._player_repo.get_by_telegram_user_id(offer.player_telegram_user_id)
        if player is None:
            return None, None

        display_name = f"@{player.username}" if player.username else str(player.telegram_user_id)
        if offer.status == "revealed":
            return f"🕵️ {display_name} был раскрыт. Награда и штраф не применяются.", None
        if offer.status != "accepted" or offer.selected_quest_id is None:
            return None, None

        selected = next((item for item in offer.options if item.quest_id == offer.selected_quest_id), None)
        if selected is None:
            return None, None

        actor_messages = await self._chat_message_repo.list_messages_in_window(
            chat_id=self._group_chat_id,
            author_user_id=offer.player_telegram_user_id,
            start_at=start_at,
            end_at=end_at,
        )
        target_messages: list = []
        if selected.target_user_id is not None:
            target_messages = await self._chat_message_repo.list_messages_in_window(
                chat_id=self._group_chat_id,
                author_user_id=selected.target_user_id,
                start_at=start_at,
                end_at=end_at,
            )
        completed = await self._quest_completion_service.is_completed(
            option=selected,
            actor_messages=actor_messages,
            target_messages=target_messages,
        )
        reward_amount = selected.base_reward * (2 if offer.double_active else 1)
        penalty_amount = selected.base_penalty * (2 if offer.double_active else 1)
        if completed:
            await self._player_repo.apply_balance_change(
                telegram_user_id=offer.player_telegram_user_id,
                amount=reward_amount,
                reason="quest_reward",
            )
            await self._daily_quest_repo.set_status(
                player_telegram_user_id=offer.player_telegram_user_id,
                quest_date=offer.quest_date,
                status="completed",
            )
            return f"✅ {display_name} выполнил квест: +{reward_amount} DUB", offer.player_telegram_user_id

        await self._player_repo.apply_balance_change(
            telegram_user_id=offer.player_telegram_user_id,
            amount=-penalty_amount,
            reason="quest_penalty",
        )
        await self._daily_quest_repo.set_status(
            player_telegram_user_id=offer.player_telegram_user_id,
            quest_date=offer.quest_date,
            status="failed",
        )
        return f"❌ {display_name} не выполнил квест: -{penalty_amount} DUB", None

    async def _settle_jackpot(self, quest_date, eligible_player_ids: list[int]) -> str | None:  # type: ignore[no-untyped-def]
        jackpot_total = await self._jackpot_repo.get_total_for_date(quest_date)
        if jackpot_total <= 0:
            return None
        if not eligible_player_ids:
            await self._jackpot_repo.set_carryover(jackpot_total)
            return f"🎰 Jackpot {jackpot_total} DUB перенесён на следующий день."

        winner_telegram_user_id = random.choice(eligible_player_ids)
        winner = await self._player_repo.get_by_telegram_user_id(winner_telegram_user_id)
        winner_name = (
            f"@{winner.username}" if winner and winner.username else str(winner_telegram_user_id)
        )
        await self._player_repo.apply_balance_change(
            telegram_user_id=winner_telegram_user_id,
            amount=jackpot_total,
            reason="jackpot_win",
        )
        await self._jackpot_repo.set_carryover(0)
        return f"🎰 Jackpot {jackpot_total} DUB забирает {winner_name}"
