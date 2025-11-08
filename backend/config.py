import os
from dataclasses import dataclass, field
from typing import List

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
    validation_errors: List[str] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        if not self.perplexity_api_key:
            self.validation_errors.append("PERPLEXITY_API_KEY가 설정되지 않았습니다.")
        elif not self.perplexity_api_key.startswith(("pk-", "sk-", "pplx-")):
            self.validation_errors.append("PERPLEXITY_API_KEY 형식이 올바르지 않습니다 (pk-로 시작해야 합니다).")

    @property
    def perplexity_enabled(self) -> bool:
        return len(self.validation_errors) == 0


settings = Settings()
