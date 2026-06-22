from dataclasses import dataclass


@dataclass(frozen=True)
class Player:
    id: int
    telegram_user_id: int
    username: str | None
    first_name: str | None
    private_chat_id: int | None
    balance_dub: int
    shield_count: int
    is_active: bool
    is_admin: bool
