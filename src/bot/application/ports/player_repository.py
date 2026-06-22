from typing import Protocol

from bot.domain.player import Player


class PlayerRepository(Protocol):
    async def get_by_telegram_user_id(self, telegram_user_id: int) -> Player | None:
        ...

    async def get_by_username(self, username: str) -> Player | None:
        ...

    async def create(
        self,
        telegram_user_id: int,
        username: str | None,
        first_name: str | None,
        starting_balance: int,
    ) -> Player:
        ...

    async def update_private_chat_id(self, telegram_user_id: int, private_chat_id: int) -> None:
        ...

    async def top_by_balance(self, limit: int) -> list[Player]:
        ...

    async def list_active_with_private_chat(self) -> list[Player]:
        ...

    async def apply_balance_change(self, telegram_user_id: int, amount: int, reason: str) -> Player | None:
        ...

    async def set_balance(self, telegram_user_id: int, new_balance: int, reason: str) -> Player | None:
        ...

    async def add_shield(self, telegram_user_id: int, delta: int) -> Player | None:
        ...
