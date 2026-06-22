# Quests Guide

## Location

- Main quest catalog file: `quests/quests.json`

## Quest schema

Each quest object supports:

- `id` (string, unique)
- `enabled` (bool)
- `difficulty` (`easy` | `medium` | `hard`)
- `base_reward` (int)
- `base_penalty` (int)
- `requires_target` (bool)
- `target_type` (string)
- `title` (string)
- `description_template` (string) — private text shown to performer
- `public_solution` (string) — semantic meaning used in `/guess` and AI checks
- `hint_text` (optional string) — explicit hint text for `/buy hint`; if absent, bot uses generic hint by validation type
- `validation` (object):
  - `type`: `message_contains_text` | `reply_contains_text` | `reply_to_target_contains_text` | `custom_ai_check`
  - `must_be_reply` (optional bool)
  - `text_contains_any` (optional string array)
  - `target_required` (optional bool)
- `ai_validation` (object):
  - `enabled` (bool)

## Validation behavior

- Rule-based validation is used for:
  - `message_contains_text`
  - `reply_contains_text`
  - `reply_to_target_contains_text`
- Semantic validation (OpenAI + fallback heuristic) is used for:
  - `validation.type = custom_ai_check`
  - or `ai_validation.enabled = true`

## Example: rule-based quest

```json
{
  "id": "say_keyword",
  "enabled": true,
  "difficulty": "easy",
  "base_reward": 100,
  "base_penalty": 50,
  "requires_target": false,
  "target_type": "none",
  "title": "Keyword message",
  "description_template": "Напиши сообщение со словом \"пельмени\".",
  "public_solution": "Игрок должен написать сообщение с ключевым словом.",
  "validation": {
    "type": "message_contains_text",
    "text_contains_any": ["пельмени"]
  },
  "ai_validation": {
    "enabled": false
  }
}
```

## Example: semantic quest

```json
{
  "id": "indirect_target_action",
  "enabled": true,
  "difficulty": "hard",
  "base_reward": 600,
  "base_penalty": 250,
  "requires_target": true,
  "target_type": "random_active_player",
  "title": "Force target reaction",
  "description_template": "Сделай так, чтобы target сам написал нужное слово.",
  "public_solution": "Игрок должен спровоцировать target на нужное действие.",
  "validation": {
    "type": "custom_ai_check"
  },
  "ai_validation": {
    "enabled": true
  }
}
```

## Reloading quests without restart

- Admin command: `/admin_reload_quests`
