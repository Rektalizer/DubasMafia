import json
from dataclasses import dataclass

import aiohttp

from bot.application.ports.semantic_evaluator import SemanticEvaluation, SemanticEvaluator
from bot.domain.chat_message import ChatMessage


@dataclass(frozen=True, slots=True)
class OpenAIConfig:
    api_key: str
    model: str
    timeout_seconds: int = 25


class OpenAISemanticEvaluator(SemanticEvaluator):
    def __init__(self, config: OpenAIConfig, fallback: SemanticEvaluator) -> None:
        self._config = config
        self._fallback = fallback

    async def evaluate_guess(
        self,
        public_solution: str,
        guess_text: str,
    ) -> SemanticEvaluation:
        if not self._config.api_key:
            return await self._fallback.evaluate_guess(public_solution=public_solution, guess_text=guess_text)

        prompt = (
            "Ты валидатор совпадения смысла догадки с заданием. "
            "Верни ТОЛЬКО JSON: "
            '{"guessed": true|false, "confidence": 0..1, "reason": "..."}. '
            f"Публичный смысл задания: {public_solution}\n"
            f"Текст догадки: {guess_text}"
        )
        payload = await self._request_json(prompt)
        return SemanticEvaluation(
            matched=bool(payload.get("guessed", False)),
            confidence=float(payload.get("confidence", 0.0)),
            reason=str(payload.get("reason", "openai")),
        )

    async def evaluate_quest_completion(
        self,
        description_for_player: str,
        public_solution: str,
        actor_messages: list[ChatMessage],
        target_messages: list[ChatMessage],
    ) -> SemanticEvaluation:
        if not self._config.api_key:
            return await self._fallback.evaluate_quest_completion(
                description_for_player=description_for_player,
                public_solution=public_solution,
                actor_messages=actor_messages,
                target_messages=target_messages,
            )

        actor_lines = [f"- {msg.text or ''}" for msg in actor_messages[-25:]]
        target_lines = [f"- {msg.text or ''}" for msg in target_messages[-25:]]
        prompt = (
            "Ты валидатор выполнения квеста. Верни ТОЛЬКО JSON: "
            '{"completed": true|false, "confidence": 0..1, "reason": "..."}.\n'
            f"Описание квеста: {description_for_player}\n"
            f"Публичный смысл: {public_solution}\n"
            "Сообщения исполнителя:\n"
            + ("\n".join(actor_lines) if actor_lines else "-")
            + "\nСообщения target (если есть):\n"
            + ("\n".join(target_lines) if target_lines else "-")
        )
        payload = await self._request_json(prompt)
        return SemanticEvaluation(
            matched=bool(payload.get("completed", False)),
            confidence=float(payload.get("confidence", 0.0)),
            reason=str(payload.get("reason", "openai")),
        )

    async def _request_json(self, prompt: str) -> dict:
        headers = {
            "Authorization": f"Bearer {self._config.api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self._config.model,
            "messages": [
                {"role": "system", "content": "Return only strict JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }
        timeout = aiohttp.ClientTimeout(total=self._config.timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=body,
            ) as response:
                response.raise_for_status()
                raw = await response.json()
        content = raw["choices"][0]["message"]["content"]
        return json.loads(content)
