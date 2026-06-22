from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.domain.quest import DailyQuestOffer, DailyQuestOption, QuestDifficulty, QuestValidationRule
from bot.infrastructure.db.models import DailyQuestOfferModel


class SQLAlchemyDailyQuestRepository:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def save_offer(self, offer: DailyQuestOffer) -> None:
        async with self._session_factory() as session:
            query = select(DailyQuestOfferModel).where(
                DailyQuestOfferModel.player_telegram_user_id == offer.player_telegram_user_id,
                DailyQuestOfferModel.quest_date == offer.quest_date,
            )
            result = await session.execute(query)
            existing = result.scalar_one_or_none()
            payload = [self._option_to_json(option) for option in offer.options]

            if existing is None:
                session.add(
                    DailyQuestOfferModel(
                        player_telegram_user_id=offer.player_telegram_user_id,
                        quest_date=offer.quest_date,
                        options_json=payload,
                        selected_difficulty=offer.selected_difficulty.value
                        if offer.selected_difficulty
                        else None,
                        selected_quest_id=offer.selected_quest_id,
                        status=offer.status,
                        double_active=offer.double_active,
                        accepted_at=offer.accepted_at,
                    )
                )
            else:
                existing.options_json = payload
                existing.selected_difficulty = (
                    offer.selected_difficulty.value if offer.selected_difficulty else None
                )
                existing.selected_quest_id = offer.selected_quest_id
                existing.status = offer.status
                existing.double_active = offer.double_active
                existing.accepted_at = offer.accepted_at
            await session.commit()

    async def get_offer(self, player_telegram_user_id: int, quest_date: date) -> DailyQuestOffer | None:
        async with self._session_factory() as session:
            query = select(DailyQuestOfferModel).where(
                DailyQuestOfferModel.player_telegram_user_id == player_telegram_user_id,
                DailyQuestOfferModel.quest_date == quest_date,
            )
            result = await session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                return None
            return self._to_domain(model)

    async def set_selected(
        self,
        player_telegram_user_id: int,
        quest_date: date,
        selected_difficulty: QuestDifficulty,
    ) -> DailyQuestOffer | None:
        async with self._session_factory() as session:
            query = select(DailyQuestOfferModel).where(
                DailyQuestOfferModel.player_telegram_user_id == player_telegram_user_id,
                DailyQuestOfferModel.quest_date == quest_date,
            )
            result = await session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                return None

            options = [self._option_from_json(row) for row in model.options_json]
            selected = next((item for item in options if item.difficulty == selected_difficulty), None)
            if selected is None:
                return None

            model.selected_difficulty = selected_difficulty.value
            model.selected_quest_id = selected.quest_id
            model.status = "accepted"
            model.accepted_at = datetime.now(UTC)
            await session.commit()
            return self._to_domain(model)

    async def set_revealed(self, player_telegram_user_id: int, quest_date: date) -> DailyQuestOffer | None:
        async with self._session_factory() as session:
            query = select(DailyQuestOfferModel).where(
                DailyQuestOfferModel.player_telegram_user_id == player_telegram_user_id,
                DailyQuestOfferModel.quest_date == quest_date,
            )
            result = await session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                return None
            model.status = "revealed"
            await session.commit()
            return self._to_domain(model)

    async def list_by_date(self, quest_date: date) -> list[DailyQuestOffer]:
        async with self._session_factory() as session:
            query = select(DailyQuestOfferModel).where(DailyQuestOfferModel.quest_date == quest_date)
            result = await session.execute(query)
            models = result.scalars().all()
            return [self._to_domain(model) for model in models]

    async def set_status(
        self,
        player_telegram_user_id: int,
        quest_date: date,
        status: str,
    ) -> DailyQuestOffer | None:
        async with self._session_factory() as session:
            query = select(DailyQuestOfferModel).where(
                DailyQuestOfferModel.player_telegram_user_id == player_telegram_user_id,
                DailyQuestOfferModel.quest_date == quest_date,
            )
            result = await session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                return None
            model.status = status
            await session.commit()
            return self._to_domain(model)

    async def set_double_active(self, player_telegram_user_id: int, quest_date: date) -> DailyQuestOffer | None:
        async with self._session_factory() as session:
            query = select(DailyQuestOfferModel).where(
                DailyQuestOfferModel.player_telegram_user_id == player_telegram_user_id,
                DailyQuestOfferModel.quest_date == quest_date,
            )
            result = await session.execute(query)
            model = result.scalar_one_or_none()
            if model is None:
                return None
            model.double_active = True
            await session.commit()
            return self._to_domain(model)

    @staticmethod
    def _option_to_json(option: DailyQuestOption) -> dict:
        return {
            "quest_id": option.quest_id,
            "difficulty": option.difficulty.value,
            "base_reward": option.base_reward,
            "base_penalty": option.base_penalty,
            "description_for_player": option.description_for_player,
            "public_solution": option.public_solution,
            "validation_rule": {
                "validation_type": option.validation_rule.validation_type,
                "must_be_reply": option.validation_rule.must_be_reply,
                "text_contains_any": option.validation_rule.text_contains_any,
                "target_required": option.validation_rule.target_required,
            },
            "ai_validation_enabled": option.ai_validation_enabled,
            "target_user_id": option.target_user_id,
            "hint_text": option.hint_text,
        }

    @staticmethod
    def _option_from_json(payload: dict) -> DailyQuestOption:
        return DailyQuestOption(
            quest_id=payload["quest_id"],
            difficulty=QuestDifficulty(payload["difficulty"]),
            base_reward=payload["base_reward"],
            base_penalty=payload["base_penalty"],
            description_for_player=payload["description_for_player"],
            public_solution=payload["public_solution"],
            validation_rule=QuestValidationRule(
                validation_type=payload.get("validation_rule", {}).get(
                    "validation_type",
                    "message_contains_text",
                ),
                must_be_reply=payload.get("validation_rule", {}).get("must_be_reply", False),
                text_contains_any=payload.get("validation_rule", {}).get("text_contains_any", []),
                target_required=payload.get("validation_rule", {}).get("target_required", False),
            ),
            ai_validation_enabled=payload.get("ai_validation_enabled", False),
            target_user_id=payload.get("target_user_id"),
            hint_text=payload.get("hint_text"),
        )

    def _to_domain(self, model: DailyQuestOfferModel) -> DailyQuestOffer:
        return DailyQuestOffer(
            player_telegram_user_id=model.player_telegram_user_id,
            quest_date=model.quest_date,
            options=[self._option_from_json(row) for row in model.options_json],
            selected_difficulty=QuestDifficulty(model.selected_difficulty)
            if model.selected_difficulty
            else None,
            selected_quest_id=model.selected_quest_id,
            status=model.status,
            double_active=model.double_active,
            accepted_at=model.accepted_at,
        )
