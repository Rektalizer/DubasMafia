from bot.application.ports.semantic_evaluator import SemanticEvaluator
from bot.domain.chat_message import ChatMessage
from bot.domain.quest import DailyQuestOption


class QuestCompletionService:
    def __init__(self, semantic_evaluator: SemanticEvaluator, ai_confidence_threshold: float) -> None:
        self._semantic_evaluator = semantic_evaluator
        self._ai_confidence_threshold = ai_confidence_threshold

    async def is_completed(
        self,
        option: DailyQuestOption,
        actor_messages: list[ChatMessage],
        target_messages: list[ChatMessage],
    ) -> bool:
        validation_type = option.validation_rule.validation_type
        if validation_type == "custom_ai_check" or option.ai_validation_enabled:
            evaluation = await self._semantic_evaluator.evaluate_quest_completion(
                description_for_player=option.description_for_player,
                public_solution=option.public_solution,
                actor_messages=actor_messages,
                target_messages=target_messages,
            )
            return evaluation.matched and evaluation.confidence >= self._ai_confidence_threshold

        if validation_type == "message_contains_text":
            return self._message_contains_text(actor_messages, option.validation_rule.text_contains_any)
        if validation_type == "reply_contains_text":
            return self._reply_contains_text(actor_messages, option.validation_rule.text_contains_any)
        if validation_type == "reply_to_target_contains_text":
            return self._reply_to_target_contains_text(
                actor_messages=actor_messages,
                target_user_id=option.target_user_id,
                needles=option.validation_rule.text_contains_any,
            )
        return False

    @staticmethod
    def _message_contains_text(messages: list[ChatMessage], needles: list[str]) -> bool:
        if not needles:
            return bool(messages)
        lowered = [needle.lower() for needle in needles]
        for message in messages:
            text = (message.text or "").lower()
            if any(needle in text for needle in lowered):
                return True
        return False

    def _reply_contains_text(self, messages: list[ChatMessage], needles: list[str]) -> bool:
        reply_messages = [msg for msg in messages if msg.replied_message_id is not None]
        return self._message_contains_text(reply_messages, needles)

    def _reply_to_target_contains_text(
        self,
        actor_messages: list[ChatMessage],
        target_user_id: int | None,
        needles: list[str],
    ) -> bool:
        if target_user_id is None:
            return False
        candidates = [
            message
            for message in actor_messages
            if message.replied_message_id is not None and message.replied_author_user_id == target_user_id
        ]
        return self._message_contains_text(candidates, needles)
