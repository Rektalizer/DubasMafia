import asyncio
from contextlib import suppress
from datetime import datetime
import logging
from pathlib import Path
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher

from bot.application.services.chat_message_service import ChatMessageService
from bot.application.services.admin_command_service import AdminCommandService
from bot.application.services.admin_observability_service import AdminObservabilityService
from bot.application.services.daily_quest_service import DailyQuestService
from bot.application.services.guess_service import GuessService
from bot.application.services.offer_scheduler_service import OfferSchedulerService
from bot.application.services.player_service import PlayerService
from bot.application.services.quest_completion_service import QuestCompletionService
from bot.application.services.quest_catalog_service import QuestCatalogService
from bot.application.services.round_settlement_service import RoundSettlementService
from bot.application.services.schedule_service import ScheduleService
from bot.application.services.shop_service import ShopService, ShopSettings
from bot.application.services.system_service import SystemService
from bot.config import get_settings
from bot.domain.scheduling import GameMode
from bot.infrastructure.clock import SystemClock
from bot.infrastructure.db.repositories.chat_message_repository import SQLAlchemyChatMessageRepository
from bot.infrastructure.db.repositories.admin_read_repository import SQLAlchemyAdminReadRepository
from bot.infrastructure.db.repositories.daily_quest_repository import SQLAlchemyDailyQuestRepository
from bot.infrastructure.db.repositories.jackpot_repository import SQLAlchemyJackpotRepository
from bot.infrastructure.db.repositories.shop_action_repository import SQLAlchemyShopActionRepository
from bot.infrastructure.db.repositories.player_repository import SQLAlchemyPlayerRepository
from bot.infrastructure.db.session import create_engine, create_session_factory
from bot.infrastructure.logging import setup_logging
from bot.infrastructure.openai_semantic_evaluator import OpenAIConfig, OpenAISemanticEvaluator
from bot.infrastructure.semantic_evaluator import HeuristicSemanticEvaluator
from bot.presentation.routers.daily_quests import (
    build_offer_keyboard,
    build_offer_text,
    create_daily_quest_router,
)
from bot.presentation.routers.admin import create_admin_router
from bot.presentation.routers.guesses import create_guess_router
from bot.presentation.routers.message_capture import create_message_capture_router
from bot.presentation.routers.players import create_player_router
from bot.presentation.routers.shop import create_shop_router
from bot.presentation.routers.system import create_system_router

logger = logging.getLogger(__name__)


async def run_offer_scheduler_loop(
    bot: Bot,
    scheduler_service: OfferSchedulerService,
    settlement_service: RoundSettlementService,
    group_chat_id: int,
    timezone_name: str,
) -> None:
    timezone = ZoneInfo(timezone_name)

    async def offer_sender(player, offer) -> None:
        if player.private_chat_id is None:
            return
        await bot.send_message(
            chat_id=player.private_chat_id,
            text=build_offer_text(offer=offer),
            reply_markup=build_offer_keyboard(),
        )

    while True:
        now = datetime.now(timezone)
        await scheduler_service.tick(now=now, offer_sender=offer_sender)
        settlement_report = await settlement_service.settle_if_due(now=now)
        if settlement_report:
            await bot.send_message(chat_id=group_chat_id, text=settlement_report)
        await asyncio.sleep(15)


async def run() -> None:
    settings = get_settings()
    if not settings.bot_token:
        msg = "TELEGRAM_BOT_TOKEN is not configured"
        raise RuntimeError(msg)

    setup_logging()
    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    engine = create_engine(settings=settings)
    session_factory = create_session_factory(engine=engine)
    player_repo = SQLAlchemyPlayerRepository(session_factory=session_factory)
    daily_quest_repo = SQLAlchemyDailyQuestRepository(session_factory=session_factory)
    chat_message_repo = SQLAlchemyChatMessageRepository(session_factory=session_factory)
    admin_read_repo = SQLAlchemyAdminReadRepository(session_factory=session_factory)
    jackpot_repo = SQLAlchemyJackpotRepository(session_factory=session_factory)
    shop_action_repo = SQLAlchemyShopActionRepository(session_factory=session_factory)

    system_service = SystemService(schedule_config=settings.game_schedule_config())
    schedule_service = ScheduleService(config=settings.game_schedule_config())
    player_service = PlayerService(
        player_repo=player_repo,
        starting_balance=settings.starting_balance,
    )
    daily_quest_service = DailyQuestService(repo=daily_quest_repo)
    quest_catalog_service = QuestCatalogService(quests_file_path=Path(settings.quests_file_path))
    chat_message_service = ChatMessageService(repo=chat_message_repo)
    semantic_evaluator = OpenAISemanticEvaluator(
        config=OpenAIConfig(api_key=settings.openai_api_key, model=settings.openai_model),
        fallback=HeuristicSemanticEvaluator(),
    )
    quest_completion_service = QuestCompletionService(
        semantic_evaluator=semantic_evaluator,
        ai_confidence_threshold=settings.quest_ai_confidence_threshold,
    )
    test_round_anchor = datetime.now(ZoneInfo(settings.timezone)) if settings.game_mode == GameMode.TEST else None
    offer_scheduler_service = OfferSchedulerService(
        schedule_service=schedule_service,
        daily_quest_service=daily_quest_service,
        player_repo=player_repo,
        quest_catalog_service=quest_catalog_service,
        test_round_anchor=test_round_anchor,
    )
    round_settlement_service = RoundSettlementService(
        schedule_service=schedule_service,
        daily_quest_repo=daily_quest_repo,
        player_repo=player_repo,
        chat_message_repo=chat_message_repo,
        jackpot_repo=jackpot_repo,
        quest_completion_service=quest_completion_service,
        group_chat_id=settings.group_chat_id,
        test_round_anchor=test_round_anchor,
    )
    guess_service = GuessService(
        player_repo=player_repo,
        daily_quest_repo=daily_quest_repo,
        schedule_service=schedule_service,
        semantic_evaluator=semantic_evaluator,
        guess_confidence_threshold=settings.guess_confidence_threshold,
        test_round_anchor=test_round_anchor,
    )
    shop_service = ShopService(
        player_repo=player_repo,
        daily_quest_repo=daily_quest_repo,
        jackpot_repo=jackpot_repo,
        daily_quest_service=daily_quest_service,
        quest_catalog_service=quest_catalog_service,
        shop_action_repo=shop_action_repo,
        schedule_service=schedule_service,
        settings=ShopSettings(
            shield_price=settings.shield_price,
            double_price=settings.double_price,
            reroll_price=settings.reroll_price,
            hint_price=settings.hint_price,
            mute_price=settings.mute_price,
            mute_duration_minutes=settings.mute_duration_minutes,
            mute_cooldown_minutes=settings.mute_cooldown_minutes,
            jackpot_min=settings.jackpot_min,
            jackpot_max_per_day=settings.jackpot_max_per_day,
        ),
        test_round_anchor=test_round_anchor,
    )
    admin_command_service = AdminCommandService(
        admin_user_ids=set(settings.admin_user_ids),
        offer_scheduler_service=offer_scheduler_service,
        settlement_service=round_settlement_service,
        player_repo=player_repo,
        quest_catalog_service=quest_catalog_service,
        timezone_name=settings.timezone,
    )
    admin_observability_service = AdminObservabilityService(
        admin_user_ids=set(settings.admin_user_ids),
        schedule_service=schedule_service,
        admin_read_repo=admin_read_repo,
        timezone_name=settings.timezone,
        test_round_anchor=test_round_anchor,
    )
    clock = SystemClock()
    dispatcher.include_router(create_system_router(system_service=system_service, clock=clock))
    dispatcher.include_router(create_player_router(player_service=player_service))
    dispatcher.include_router(
        create_daily_quest_router(
            daily_quest_service=daily_quest_service,
            quest_catalog_service=quest_catalog_service,
            schedule_service=schedule_service,
            timezone_name=settings.timezone,
            group_chat_id=settings.group_chat_id,
            test_round_anchor=test_round_anchor,
        )
    )
    dispatcher.include_router(create_message_capture_router(chat_message_service=chat_message_service))
    dispatcher.include_router(create_guess_router(guess_service=guess_service, timezone_name=settings.timezone))
    dispatcher.include_router(
        create_shop_router(
            shop_service=shop_service,
            timezone_name=settings.timezone,
            group_chat_id=settings.group_chat_id,
            admin_user_ids=set(settings.admin_user_ids),
        )
    )

    async def admin_offer_sender(player, offer) -> None:
        if player.private_chat_id is None:
            return
        await bot.send_message(
            chat_id=player.private_chat_id,
            text=build_offer_text(offer=offer),
            reply_markup=build_offer_keyboard(),
        )

    dispatcher.include_router(
        create_admin_router(
            admin_command_service=admin_command_service,
            admin_observability_service=admin_observability_service,
            offer_sender=admin_offer_sender,
            group_chat_id=settings.group_chat_id,
        )
    )

    logger.info("Starting bot in %s mode", settings.game_mode.value)
    scheduler_task = asyncio.create_task(
        run_offer_scheduler_loop(
            bot=bot,
            scheduler_service=offer_scheduler_service,
            settlement_service=round_settlement_service,
            group_chat_id=settings.group_chat_id,
            timezone_name=settings.timezone,
        )
    )
    try:
        await dispatcher.start_polling(bot)
    finally:
        scheduler_task.cancel()
        with suppress(asyncio.CancelledError):
            await scheduler_task
        await engine.dispose()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
