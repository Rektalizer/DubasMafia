from dataclasses import dataclass

import pytest

from bot.application.services.player_service import PlayerService
from bot.domain.player import Player


@dataclass
class InMemoryPlayerRepo:
    players: dict[int, Player]

    async def get_by_telegram_user_id(self, telegram_user_id: int) -> Player | None:
        return self.players.get(telegram_user_id)

    async def get_by_username(self, username: str) -> Player | None:
        for player in self.players.values():
            if player.username == username:
                return player
        return None

    async def create(
        self,
        telegram_user_id: int,
        username: str | None,
        first_name: str | None,
        starting_balance: int,
    ) -> Player:
        player = Player(
            id=len(self.players) + 1,
            telegram_user_id=telegram_user_id,
            username=username,
            first_name=first_name,
            private_chat_id=None,
            balance_dub=starting_balance,
            shield_count=0,
            is_active=True,
            is_admin=False,
        )
        self.players[telegram_user_id] = player
        return player

    async def update_private_chat_id(self, telegram_user_id: int, private_chat_id: int) -> None:
        player = self.players.get(telegram_user_id)
        if player is None:
            return
        self.players[telegram_user_id] = Player(
            **{**player.__dict__, "private_chat_id": private_chat_id}
        )

    async def top_by_balance(self, limit: int) -> list[Player]:
        return sorted(self.players.values(), key=lambda p: p.balance_dub, reverse=True)[:limit]

    async def list_active_with_private_chat(self) -> list[Player]:
        return [player for player in self.players.values() if player.is_active and player.private_chat_id]


@pytest.mark.asyncio
async def test_join_creates_new_player() -> None:
    service = PlayerService(player_repo=InMemoryPlayerRepo(players={}), starting_balance=1000)
    text = await service.join(telegram_user_id=100, username="ivan", first_name="Ivan")
    assert "Ты в игре" in text


@pytest.mark.asyncio
async def test_join_existing_player_returns_already_registered() -> None:
    repo = InMemoryPlayerRepo(
        players={
            100: Player(
                id=1,
                telegram_user_id=100,
                username="ivan",
                first_name="Ivan",
                private_chat_id=None,
                balance_dub=1000,
                shield_count=0,
                is_active=True,
                is_admin=False,
            )
        }
    )
    service = PlayerService(player_repo=repo, starting_balance=1000)
    text = await service.join(telegram_user_id=100, username="ivan", first_name="Ivan")
    assert text == "Ты уже в игре."


@pytest.mark.asyncio
async def test_connect_private_chat_for_registered_user() -> None:
    repo = InMemoryPlayerRepo(
        players={
            100: Player(
                id=1,
                telegram_user_id=100,
                username="ivan",
                first_name="Ivan",
                private_chat_id=None,
                balance_dub=1000,
                shield_count=0,
                is_active=True,
                is_admin=False,
            )
        }
    )
    service = PlayerService(player_repo=repo, starting_balance=1000)
    text = await service.connect_private_chat(telegram_user_id=100, private_chat_id=777)
    assert "Личка подключена. Теперь я смогу присылать" in text


@pytest.mark.asyncio
async def test_wallet_text_asks_to_join_if_missing() -> None:
    service = PlayerService(player_repo=InMemoryPlayerRepo(players={}), starting_balance=1000)
    text = await service.wallet_text(telegram_user_id=100)
    assert "Сначала подключись к игре" in text
