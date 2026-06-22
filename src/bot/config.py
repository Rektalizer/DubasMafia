from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from bot.domain.scheduling import GameMode, GameScheduleConfig


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    group_chat_id: int = Field(default=0, alias="GROUP_CHAT_ID")
    database_url: str = Field(default="", alias="DATABASE_URL")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")
    quests_file_path: str = Field(default="quests/quests.json", alias="QUESTS_FILE_PATH")
    timezone: str = Field(default="Europe/Moscow", alias="TIMEZONE")

    game_mode: GameMode = Field(default=GameMode.PRODUCTION, alias="GAME_MODE")
    offer_hour: int = Field(default=8, alias="QUEST_OFFER_HOUR")
    offer_minute: int = Field(default=0, alias="QUEST_OFFER_MINUTE")
    check_hour: int = Field(default=20, alias="QUEST_CHECK_HOUR")
    check_minute: int = Field(default=0, alias="QUEST_CHECK_MINUTE")
    test_round_duration_minutes: int = Field(default=10, alias="TEST_ROUND_DURATION_MINUTES")
    starting_balance: int = Field(default=1000, alias="STARTING_BALANCE")
    guess_confidence_threshold: float = Field(default=0.75, alias="GUESS_CONFIDENCE_THRESHOLD")
    quest_ai_confidence_threshold: float = Field(
        default=0.70,
        alias="QUEST_AI_CONFIDENCE_THRESHOLD",
    )
    admin_user_ids_raw: str = Field(default="", alias="ADMIN_USER_IDS")
    shield_price: int = Field(default=700, alias="PRICE_SHIELD")
    double_price: int = Field(default=500, alias="PRICE_DOUBLE")
    reroll_price: int = Field(default=150, alias="PRICE_REROLL")
    hint_price: int = Field(default=300, alias="PRICE_HINT")
    mute_price: int = Field(default=1000, alias="PRICE_MUTE")
    mute_duration_minutes: int = Field(default=5, alias="MUTE_DURATION_MINUTES")
    mute_cooldown_minutes: int = Field(default=60, alias="MUTE_COOLDOWN_MINUTES")
    jackpot_min: int = Field(default=50, alias="MIN_JACKPOT_CONTRIBUTION")
    jackpot_max_per_day: int = Field(default=500, alias="MAX_JACKPOT_CONTRIBUTION_PER_DAY")

    @property
    def admin_user_ids(self) -> list[int]:
        if not self.admin_user_ids_raw.strip():
            return []
        parts = [part.strip() for part in self.admin_user_ids_raw.split(",") if part.strip()]
        return [int(part) for part in parts]

    def game_schedule_config(self) -> GameScheduleConfig:
        return GameScheduleConfig(
            mode=self.game_mode,
            timezone=self.timezone,
            offer_hour=self.offer_hour,
            offer_minute=self.offer_minute,
            check_hour=self.check_hour,
            check_minute=self.check_minute,
            test_round_duration_minutes=self.test_round_duration_minutes,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
