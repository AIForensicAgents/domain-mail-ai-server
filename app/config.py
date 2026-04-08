import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


def _bool(val: str | None, default: bool) -> bool:
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "t", "yes", "y"}


@dataclass
class Settings:
    # App
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "http://127.0.0.1:8000")

    # Security / Auth
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-prod")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

    # OpenAI
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-5.4")
    ORG_ID: str | None = os.getenv("ORG_ID")
    SYSTEM_PROMPT: str = os.getenv("SYSTEM_PROMPT", "You are a helpful, concise email assistant.")
    MAX_TOKENS_WINDOW: int = int(os.getenv("MAX_TOKENS_WINDOW", "10000"))
    MAX_COMPLETION_TOKENS: int = int(os.getenv("MAX_COMPLETION_TOKENS", "512"))

    # Inbound Webhook
    INBOUND_API_TOKEN: str = os.getenv("INBOUND_API_TOKEN", "change-in-prod")

    # SMTP Outbound
    SMTP_HOST: str = os.getenv("SMTP_HOST", "localhost")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str | None = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: str | None = os.getenv("SMTP_PASSWORD")
    SMTP_USE_TLS: bool = _bool(os.getenv("SMTP_USE_TLS"), True)
    SMTP_USE_SSL: bool = _bool(os.getenv("SMTP_USE_SSL"), False)
    FROM_FALLBACK_EMAIL: str = os.getenv("FROM_FALLBACK_EMAIL", "noreply@example.com")

    # Delegated operations
    DELEGATED_EMAIL: str | None = os.getenv("DELEGATED_EMAIL")


settings = Settings()
