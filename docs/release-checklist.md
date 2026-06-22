# Release Checklist

Use this checklist before production rollout.

## Environment

- [ ] `.env` is configured (`TELEGRAM_BOT_TOKEN`, `DATABASE_URL`, `GROUP_CHAT_ID`, `ADMIN_USER_IDS`)
- [ ] Shop pricing and limits are configured (`PRICE_*`, `MIN_JACKPOT_CONTRIBUTION`, `MAX_JACKPOT_CONTRIBUTION_PER_DAY`)
- [ ] Schedule mode is correct (`GAME_MODE=production` for prod)

## Database

- [ ] `alembic upgrade head` completed successfully
- [ ] Core tables exist (`players`, `daily_quest_offers`, `dub_transactions`, `jackpot_contributions`, `shop_actions`)

## Bot permissions

- [ ] Bot is in target group chat
- [ ] Bot receives group messages (privacy mode configured)
- [ ] Bot has admin rights for mute functionality (restrict members)

## Smoke scenario

- [ ] `/join` in group works
- [ ] `/start` in private chat works
- [ ] Offer is received (`/quests_now` or scheduled offer)
- [ ] Quest can be accepted by button
- [ ] `/guess @user text` path works
- [ ] Settlement runs and updates balances
- [ ] `/shop` and `/buy` commands work (`reroll`, `hint`, `shield`, `double`, `mute`, `jackpot`)
- [ ] Admin commands work from admin user and are denied for non-admin user

## Quality gates

- [ ] `pytest` passes
- [ ] `ruff check .` passes
