# Testing And Operations

## 1) Setup

1. Copy env:
   - Windows: `copy .env.example .env`
2. Configure:
   - `TELEGRAM_BOT_TOKEN`
   - `GROUP_CHAT_ID`
   - `ADMIN_USER_IDS`
   - `DATABASE_URL`
3. Migrate DB:
   - `alembic upgrade head`
4. Start bot:
   - `python -m bot.main`

## 2) Fast test mode

Use short rounds:

- `GAME_MODE=test`
- `TEST_ROUND_DURATION_MINUTES=10`

In test mode, round start is anchored at bot startup.

## 3) Basic user flow

1. In group chat: `/join`
2. In bot DM: `/start`
3. In DM: `/quests_now` (manual test offer)
4. Pick difficulty button
5. Send quest-related messages in group
6. In group: `/guess @user текст`

## 4) Admin test commands

Only IDs from `ADMIN_USER_IDS` can run:

- `/admin_send_quests_now`
- `/admin_check_now`
- `/admin_status`
- `/admin_logs`
- `/admin_reload_quests`
- `/admin_give @user amount reason`
- `/admin_take @user amount reason`
- `/admin_set_balance @user amount`
- `/admin_broadcast текст`

## 5) Shop flow checks

- `/shop`
- `/buy reroll`
- `/buy hint @user`
- `/buy shield`
- `/buy double` (requires accepted quest)
- `/buy mute @user`
- `/buy jackpot 100`

## 6) Useful checks

- Run tests: `pytest`
- Lint: `ruff check src tests`
