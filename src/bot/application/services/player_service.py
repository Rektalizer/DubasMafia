from bot.application.ports.player_repository import PlayerRepository


class PlayerService:
    def __init__(self, player_repo: PlayerRepository, starting_balance: int) -> None:
        self._player_repo = player_repo
        self._starting_balance = starting_balance

    async def join(self, telegram_user_id: int, username: str | None, first_name: str | None) -> str:
        existing = await self._player_repo.get_by_telegram_user_id(telegram_user_id=telegram_user_id)
        if existing is not None:
            return "Ты уже в игре."

        await self._player_repo.create(
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
            starting_balance=self._starting_balance,
        )
        return (
            "Ты в игре. Чтобы получать тайные квесты, "
            "открой личку с ботом и нажми /start."
        )

    async def connect_private_chat(self, telegram_user_id: int, private_chat_id: int) -> str:
        existing = await self._player_repo.get_by_telegram_user_id(telegram_user_id=telegram_user_id)
        await self._player_repo.update_private_chat_id(
            telegram_user_id=telegram_user_id,
            private_chat_id=private_chat_id,
        )
        if existing is None:
            return "Личка подключена. Теперь напиши /join в игровом чате."
        return "Личка подключена. Теперь я смогу присылать тебе тайные квесты."

    async def wallet_text(self, telegram_user_id: int) -> str:
        player = await self._player_repo.get_by_telegram_user_id(telegram_user_id=telegram_user_id)
        if player is None:
            return "Сначала подключись к игре через /join в игровом чате."
        return (
            "💰 Твой кошелёк:\n"
            f"Баланс: {player.balance_dub} DUB\n"
            f"Активные щиты: {player.shield_count}"
        )

    async def leaderboard_text(self, current_telegram_user_id: int, limit: int = 10) -> str:
        players = await self._player_repo.top_by_balance(limit=limit)
        if not players:
            return "Пока нет игроков в рейтинге."
        lines = ["🏆 Лидерборд DUB"]
        for player in players:
            name = f"@{player.username}" if player.username else str(player.telegram_user_id)
            lines.append(f"{name} — {player.balance_dub} DUB")

        current = await self._player_repo.get_by_telegram_user_id(current_telegram_user_id)
        if current is None:
            return "\n".join(lines)

        all_players = await self._player_repo.top_by_balance(limit=100000)
        rank = next(
            (idx for idx, player in enumerate(all_players, start=1) if player.id == current.id),
            None,
        )
        if rank is not None and rank > limit:
            lines.append(f"Твоё место: {rank} из {len(all_players)}.")
        return "\n".join(lines)
