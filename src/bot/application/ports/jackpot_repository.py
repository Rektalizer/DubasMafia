from datetime import date
from typing import Protocol


class JackpotRepository(Protocol):
    async def get_contribution(self, quest_date: date, telegram_user_id: int) -> int:
        ...

    async def add_contribution(self, quest_date: date, telegram_user_id: int, amount: int) -> int:
        ...

    async def get_total_for_date(self, quest_date: date) -> int:
        ...

    async def get_carryover(self) -> int:
        ...

    async def set_carryover(self, amount: int) -> None:
        ...
