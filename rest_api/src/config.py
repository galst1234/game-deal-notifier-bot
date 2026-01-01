import os

ISTHEREANYDEAL_API_KEY: str = os.getenv("ISTHEREANYDEAL_API_KEY", "")
DB_USER: str = os.getenv("DB_USER", "")
DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
DB_HOST: str = os.getenv("DB_HOST", "localhost")
DB_PORT: str = os.getenv("DB_PORT", "5432")
DB_NAME: str = os.getenv("DB_NAME", "game_deal_notifier")
