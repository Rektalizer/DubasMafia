from unittest.mock import AsyncMock

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods.send_message import SendMessage

from bot.presentation.routers.daily_quests import send_group_quest_announcement


@pytest.mark.asyncio
async def test_send_group_quest_announcement_skips_when_group_chat_not_configured() -> None:
    bot = AsyncMock()

    await send_group_quest_announcement(bot=bot, group_chat_id=0, player_tag="player1")

    bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_send_group_quest_announcement_sends_message_when_group_chat_configured() -> None:
    bot = AsyncMock()

    await send_group_quest_announcement(bot=bot, group_chat_id=-100123, player_tag="player1")

    bot.send_message.assert_awaited_once()
    call = bot.send_message.await_args.kwargs
    assert call["chat_id"] == -100123
    assert "@player1" in call["text"]


@pytest.mark.asyncio
async def test_send_group_quest_announcement_handles_telegram_bad_request() -> None:
    bot = AsyncMock()
    bot.send_message.side_effect = TelegramBadRequest(
        method=SendMessage(chat_id=-100123, text="x"),
        message="chat not found",
    )

    await send_group_quest_announcement(bot=bot, group_chat_id=-100123, player_tag="player1")

    bot.send_message.assert_awaited_once()
