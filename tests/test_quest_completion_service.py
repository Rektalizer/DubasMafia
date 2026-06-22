from datetime import UTC, datetime

import pytest

from bot.application.ports.semantic_evaluator import SemanticEvaluation
from bot.application.services.quest_completion_service import QuestCompletionService
from bot.domain.chat_message import ChatMessage
from bot.domain.quest import DailyQuestOption, QuestDifficulty, QuestValidationRule


class StubSemanticEvaluator:
    def __init__(self, result: SemanticEvaluation) -> None:
        self._result = result

    async def evaluate_guess(self, public_solution: str, guess_text: str) -> SemanticEvaluation:
        del public_solution, guess_text
        return self._result

    async def evaluate_quest_completion(
        self,
        description_for_player: str,
        public_solution: str,
        actor_messages: list[ChatMessage],
        target_messages: list[ChatMessage],
    ) -> SemanticEvaluation:
        del description_for_player, public_solution, actor_messages, target_messages
        return self._result


def _message(text: str, replied_author: int | None = None) -> ChatMessage:
    return ChatMessage(
        telegram_message_id=1,
        chat_id=-100,
        author_user_id=10,
        author_username="u",
        text=text,
        replied_message_id=2 if replied_author is not None else None,
        replied_author_user_id=replied_author,
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_rule_based_message_contains_text() -> None:
    service = QuestCompletionService(
        semantic_evaluator=StubSemanticEvaluator(SemanticEvaluation(False, 0.1, "unused")),
        ai_confidence_threshold=0.7,
    )
    option = DailyQuestOption(
        quest_id="q1",
        difficulty=QuestDifficulty.EASY,
        base_reward=100,
        base_penalty=50,
        description_for_player="desc",
        public_solution="pub",
        validation_rule=QuestValidationRule(
            validation_type="message_contains_text",
            must_be_reply=False,
            text_contains_any=["пельмени"],
            target_required=False,
        ),
        ai_validation_enabled=False,
        target_user_id=None,
    )

    result = await service.is_completed(option=option, actor_messages=[_message("люблю пельмени")], target_messages=[])
    assert result is True


@pytest.mark.asyncio
async def test_custom_ai_check_uses_semantic_result() -> None:
    service = QuestCompletionService(
        semantic_evaluator=StubSemanticEvaluator(SemanticEvaluation(True, 0.9, "ok")),
        ai_confidence_threshold=0.7,
    )
    option = DailyQuestOption(
        quest_id="q2",
        difficulty=QuestDifficulty.HARD,
        base_reward=600,
        base_penalty=250,
        description_for_player="desc",
        public_solution="pub",
        validation_rule=QuestValidationRule(
            validation_type="custom_ai_check",
            must_be_reply=False,
            text_contains_any=[],
            target_required=False,
        ),
        ai_validation_enabled=True,
        target_user_id=None,
    )

    result = await service.is_completed(option=option, actor_messages=[_message("text")], target_messages=[])
    assert result is True
