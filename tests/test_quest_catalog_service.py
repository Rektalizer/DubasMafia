from pathlib import Path

from bot.application.services.quest_catalog_service import QuestCatalogService


def test_catalog_loads_enabled_quests(tmp_path: Path) -> None:
    quests_file = tmp_path / "quests.json"
    quests_file.write_text(
        """
[
  {
    "id": "q1",
    "enabled": true,
    "difficulty": "easy",
    "base_reward": 100,
    "base_penalty": 50,
    "requires_target": false,
    "target_type": "none",
    "title": "Q1",
    "description_template": "desc",
    "public_solution": "pub",
    "validation": {"type": "message_contains_text"},
    "ai_validation": {"enabled": false}
  },
  {
    "id": "q2",
    "enabled": false,
    "difficulty": "medium",
    "base_reward": 200,
    "base_penalty": 90,
    "requires_target": false,
    "target_type": "none",
    "title": "Q2",
    "description_template": "desc",
    "public_solution": "pub",
    "validation": {"type": "message_contains_text"},
    "ai_validation": {"enabled": false}
  }
]
        """.strip(),
        encoding="utf-8",
    )

    service = QuestCatalogService(quests_file_path=quests_file)
    quests = service.load_enabled()

    assert len(quests) == 1
    assert quests[0].quest_id == "q1"
