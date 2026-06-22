# DUB Quest Bot

Modular Telegram bot for the DUB Quest Game.

## Local setup

1. Create virtualenv with Python 3.12.
2. Install dependencies:
   - `pip install -e .[dev]`
3. Run tests:
   - `pytest`
4. Copy env template:
   - `copy .env.example .env` (Windows)
5. Apply migrations:
   - `alembic upgrade head`
6. Run bot:
   - `python -m bot.main`

## Time modes

- `GAME_MODE=production` uses fixed daily windows (`QUEST_OFFER_HOUR`, `QUEST_CHECK_HOUR`).
- `GAME_MODE=test` starts a short round from current time.
- Duration for test mode is controlled by `TEST_ROUND_DURATION_MINUTES` (for example `10`).

## Docker

- Start postgres + bot:
  - `docker compose up -d --build`

## CI

- GitHub Actions workflow: `.github/workflows/ci.yml`
- Runs `pytest` and `ruff check .` on push and pull requests.

## Current commands

- `/join` in group chat
- `/start` in private chat
- `/wallet`
- `/leaderboard`
- `/quests_now` in private chat (test/manual offer of 3 quests with inline pick)
- `/guess @username текст` in group chat
- `/shop`
- `/buy reroll`
- `/buy hint @user`
- `/buy shield`
- `/buy double`
- `/buy mute @user`
- `/buy jackpot amount`
- `/admin_send_quests_now` (admins only)
- `/admin_check_now` (admins only)
- `/admin_status` (admins only)
- `/admin_logs` (admins only)
- `/admin_reload_quests` (admins only)
- `/admin_give @user amount reason` (admins only)
- `/admin_take @user amount reason` (admins only)
- `/admin_set_balance @user amount` (admins only)
- `/admin_broadcast text` (admins only)

## Current automation

- Scheduler runs in background and auto-sends daily offers to active players with connected private chat.
- In `GAME_MODE=test`, the round start is fixed at bot startup and lasts `TEST_ROUND_DURATION_MINUTES`.
- At round end, settlement is executed automatically: accepted quests are marked `completed` or `failed`, balances are updated, and a daily report is sent to group chat.

## Validation modes

- Rule-based checks are used for simple quest types (`message_contains_text`, `reply_contains_text`, `reply_to_target_contains_text`).
- Semantic checks are used for `custom_ai_check` (and AI-enabled quests) via OpenAI, with fallback heuristic when OpenAI is unavailable.
- `/guess` uses semantic evaluation with `GUESS_CONFIDENCE_THRESHOLD`.

## Admin access

- Admin permissions are granted only to Telegram IDs from `ADMIN_USER_IDS` in `.env`.
- Format: `ADMIN_USER_IDS=123456,987654`

## Documentation

- Quest authoring: `docs/quests.md`
- Run/test guide: `docs/testing.md`
- Release checklist: `docs/release-checklist.md`

## Shop config

- `PRICE_SHIELD`
- `PRICE_DOUBLE`
- `PRICE_REROLL`
- `PRICE_HINT`
- `PRICE_MUTE`
- `MUTE_DURATION_MINUTES`
- `MUTE_COOLDOWN_MINUTES`
- `MIN_JACKPOT_CONTRIBUTION`
- `MAX_JACKPOT_CONTRIBUTION_PER_DAY`

## Notes

- `hint` uses `hint_text` from quest JSON when present; otherwise uses generic fallback by validation type.
- `admin_status` now includes current jackpot amount (day total + carryover).
