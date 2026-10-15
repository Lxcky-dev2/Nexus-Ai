import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    discord_token: str = os.getenv("DISCORD_BOT_TOKEN", "")
    pollinations_api_key: str = os.getenv("POLLINATIONS_API_KEY", "")
    pollinations_model: str = os.getenv("POLLINATIONS_MODEL", "openai/gpt-5.4-nano")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    sync_commands: bool = os.getenv("SYNC_COMMANDS", "true").lower() == "true"
    max_ai_chars: int = int(os.getenv("MAX_AI_CHARS", "4000"))
    ai_user_cooldown_seconds: int = int(os.getenv("AI_USER_COOLDOWN_SECONDS", "8"))
    ai_user_requests_per_minute: int = int(os.getenv("AI_USER_REQUESTS_PER_MINUTE", "5"))
    ai_guild_requests_per_minute: int = int(os.getenv("AI_GUILD_REQUESTS_PER_MINUTE", "20"))
    ai_max_concurrent: int = int(os.getenv("AI_MAX_CONCURRENT", "2"))

settings = Settings()
