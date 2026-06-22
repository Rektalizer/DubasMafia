from dataclasses import dataclass
from typing import Protocol

from bot.domain.chat_message import ChatMessage


@dataclass(frozen=True, slots=True)
class SemanticEvaluation:
    matched: bool
    confidence: float
    reason: str


class SemanticEvaluator(Protocol):
    async def evaluate_guess(
        self,
        public_solution: str,
        guess_text: str,
    ) -> SemanticEvaluation:
        ...

    async def evaluate_quest_completion(
        self,
        description_for_player: str,
        public_solution: str,
        actor_messages: list[ChatMessage],
        target_messages: list[ChatMessage],
    ) -> SemanticEvaluation:
        ...
