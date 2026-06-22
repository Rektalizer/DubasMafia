from datetime import datetime
from typing import Protocol


class ShopActionRepository(Protocol):
    async def get_last_action_at(self, action_type: str, target_telegram_user_id: int) -> datetime | None:
        ...

    async def add_action(
        self,
        action_type: str,
        buyer_telegram_user_id: int,
        target_telegram_user_id: int | None,
        result: str,
        created_at: datetime,
    ) -> None:
        ...
