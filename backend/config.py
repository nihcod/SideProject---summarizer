import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    """Centralized configuration values loaded from environment variables."""

    perplexity_api_key: str = os.getenv("PERPLEXITY_API_KEY", "")
    perplexity_model: str = os.getenv("PERPLEXITY_MODEL", "llama-3.1-sonar-small-128k-chat")
    perplexity_temperature: float = float(os.getenv("PERPLEXITY_TEMPERATURE", "0.2"))
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", "20"))


settings = Settings()
