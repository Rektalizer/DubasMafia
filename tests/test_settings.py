from bot.config import Settings
from bot.domain.scheduling import GameMode


def test_settings_parse_test_mode_from_env(monkeypatch) -> None:
    monkeypatch.setenv("GAME_MODE", "test")
    monkeypatch.setenv("TEST_ROUND_DURATION_MINUTES", "15")
    monkeypatch.setenv("TIMEZONE", "Europe/Moscow")

    settings = Settings()

    assert settings.game_mode == GameMode.TEST
    assert settings.test_round_duration_minutes == 15
    assert settings.timezone == "Europe/Moscow"


def test_settings_parse_admin_user_ids_csv(monkeypatch) -> None:
    monkeypatch.setenv("ADMIN_USER_IDS", "1,2,300")
    settings = Settings()
    assert settings.admin_user_ids == [1, 2, 300]


def test_settings_normalize_group_chat_id_from_positive(monkeypatch) -> None:
    monkeypatch.setenv("GROUP_CHAT_ID", "4335937734")
    settings = Settings()
    assert settings.group_chat_id == -1004335937734
