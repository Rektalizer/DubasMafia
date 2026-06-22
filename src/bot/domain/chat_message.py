from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ChatMessage:
    telegram_message_id: int
    chat_id: int
    author_user_id: int
    author_username: str | None
    text: str | None
    replied_message_id: int | None
    replied_author_user_id: int | None
    created_at: datetime
