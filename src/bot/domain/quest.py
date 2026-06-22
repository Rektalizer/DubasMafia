from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class QuestValidationRule:
    validation_type: str
    must_be_reply: bool
    text_contains_any: list[str]
    target_required: bool


class QuestDifficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass(frozen=True, slots=True)
class QuestTemplate:
    quest_id: str
    difficulty: QuestDifficulty
    base_reward: int
    base_penalty: int
    requires_target: bool
    target_type: str
    title: str
    description_template: str
    public_solution: str
    validation_rule: QuestValidationRule
    ai_validation_enabled: bool
    hint_text: str | None = None


@dataclass(frozen=True, slots=True)
class DailyQuestOption:
    quest_id: str
    difficulty: QuestDifficulty
    base_reward: int
    base_penalty: int
    description_for_player: str
    public_solution: str
    validation_rule: QuestValidationRule
    ai_validation_enabled: bool
    target_user_id: int | None
    hint_text: str | None = None


@dataclass(frozen=True, slots=True)
class DailyQuestOffer:
    player_telegram_user_id: int
    quest_date: date
    options: list[DailyQuestOption]
    selected_difficulty: QuestDifficulty | None
    selected_quest_id: str | None
    status: str
    double_active: bool = False
    accepted_at: datetime | None = None
