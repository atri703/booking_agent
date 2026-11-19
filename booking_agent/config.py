"""Environment configuration; JSON is deliberately the only runtime backend."""

import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()


def model_api_key_name(model: str) -> str:
    """Return the credential environment variable for a supported model identifier."""
    return "OPENROUTER_API_KEY" if model.startswith("openrouter/") else "OPENAI_API_KEY"


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path("runtime")
    timezone: str = "Asia/Kolkata"
    resource: str = "advisor"
    model: str = "openai/gpt-5.2"
    a2a_url: str = "http://127.0.0.1:8001"
    api_token: str = ""

    @classmethod
    def from_env(cls):
        result = cls(
            data_dir=Path(os.getenv("BOOKING_DATA_DIR", "runtime")),
            timezone=os.getenv("BOOKING_TIMEZONE", "Asia/Kolkata"),
            resource=os.getenv("BOOKING_RESOURCE", "advisor"),
            model=os.getenv("BOOKING_MODEL", "openai/gpt-5.2"),
            a2a_url=os.getenv("BOOKING_A2A_URL", "http://127.0.0.1:8001").rstrip("/"),
            api_token=os.getenv("BOOKING_API_TOKEN", ""),
        )
        ZoneInfo(result.timezone)
        return result
