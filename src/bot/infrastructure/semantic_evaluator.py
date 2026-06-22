import re

from bot.application.ports.semantic_evaluator import SemanticEvaluation, SemanticEvaluator
from bot.domain.chat_message import ChatMessage


class HeuristicSemanticEvaluator(SemanticEvaluator):
    async def evaluate_guess(
        self,
        public_solution: str,
        guess_text: str,
    ) -> SemanticEvaluation:
        matched = self._has_overlap(guess_text, public_solution)
        return SemanticEvaluation(
            matched=matched,
            confidence=0.8 if matched else 0.2,
            reason="heuristic_word_overlap",
        )

    async def evaluate_quest_completion(
        self,
        description_for_player: str,
        public_solution: str,
        actor_messages: list[ChatMessage],
        target_messages: list[ChatMessage],
    ) -> SemanticEvaluation:
        del description_for_player, target_messages
        actor_text = " ".join(msg.text or "" for msg in actor_messages)
        matched = self._has_overlap(actor_text, public_solution)
        return SemanticEvaluation(
            matched=matched,
            confidence=0.75 if matched else 0.25,
            reason="heuristic_actor_public_solution_overlap",
        )

    def _has_overlap(self, left: str, right: str) -> bool:
        left_words = {w for w in re.findall(r"[a-zA-Zа-яА-Я0-9]+", left.lower()) if len(w) >= 5}
        right_words = {w for w in re.findall(r"[a-zA-Zа-яА-Я0-9]+", right.lower()) if len(w) >= 5}
        return bool(left_words.intersection(right_words))
