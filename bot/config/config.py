from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str

    USE_RANDOM_DELAY_IN_RUN: bool = True
    START_DELAY: list[int] = [30, 60]

    AUTO_DO_TASKS: bool = True
    AUTO_DO_QUIZZES: bool = True

    AUTO_JOIN_CHANNELS: bool = True
    ARCHIVE_CHANNELS: bool = False

    AUTO_BUY_ANIMALS: bool = True
    MAX_ANIMALS: int = 10

    AUTO_UPGRADE_ANIMALS: bool = True

    AUTO_FEED_ANIMALS: bool = True

    COIN_TO_SAVE: int = 5000

    REF_LINK: str = 'http://t.me/zoo_story_bot/game?startapp=ref1827015632'

    TO_DO_QUEST: list[str] = [
        'telegramChannel',
        'ton_wallet_connect',
        'fakeCheck',
        'username',
        'checkCode'
    ]
    NOT_TO_DO_QUEST: list[str] = [
        'invite',
        'ton_wallet_transaction',
        'donate_ton'
    ]
    SAVE_JS_FILES: bool = False  # Experimental `True`
    ADVANCED_ANTI_DETECTION: bool = True
    ENABLE_SSL: bool = True

    USE_PROXY_FROM_FILE: bool = False
    GIT_UPDATE_CHECKER: bool = True


settings = Settings()
