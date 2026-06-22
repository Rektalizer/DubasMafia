from bot.infrastructure.db.models import Base


def test_core_tables_registered_in_metadata() -> None:
    table_names = set(Base.metadata.tables.keys())
    assert "players" in table_names
    assert "chat_messages" in table_names
    assert "dub_transactions" in table_names
    assert "daily_quest_offers" in table_names
    assert "jackpot_contributions" in table_names
