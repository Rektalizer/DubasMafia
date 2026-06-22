import json
from pathlib import Path

from bot.domain.quest import QuestDifficulty, QuestTemplate, QuestValidationRule


class QuestCatalogService:
    def __init__(self, quests_file_path: Path) -> None:
        self._quests_file_path = quests_file_path

    def load_enabled(self) -> list[QuestTemplate]:
        data = json.loads(self._quests_file_path.read_text(encoding="utf-8"))
        quests: list[QuestTemplate] = []
        for row in data:
            if not row.get("enabled", False):
                continue
            quests.append(
                QuestTemplate(
                    quest_id=row["id"],
                    difficulty=QuestDifficulty(row["difficulty"]),
                    base_reward=row["base_reward"],
                    base_penalty=row["base_penalty"],
                    requires_target=row["requires_target"],
                    target_type=row["target_type"],
                    title=row["title"],
                    description_template=row["description_template"],
                    public_solution=row["public_solution"],
                    validation_rule=QuestValidationRule(
                        validation_type=row.get("validation", {}).get("type", "message_contains_text"),
                        must_be_reply=row.get("validation", {}).get("must_be_reply", False),
                        text_contains_any=row.get("validation", {}).get("text_contains_any", []),
                        target_required=row.get("validation", {}).get("target_required", False),
                    ),
                    ai_validation_enabled=row.get("ai_validation", {}).get("enabled", False),
                    hint_text=row.get("hint_text"),
                )
            )
        return quests
