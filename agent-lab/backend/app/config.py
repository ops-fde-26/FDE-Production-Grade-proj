from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# agent-lab/.env (two levels above this file's folder: app -> backend -> agent-lab)
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    app_name: str = "agent lab"
    debug: bool = True
    # the .env variable is OPENROUTER_API_KEY
    openai_api_key: str = Field(default="", validation_alias="OPENROUTER_API_KEY")
    openai_base_url: str = "https://openrouter.ai/api/v1"
    openai_model: str = "openai/gpt-4o-mini"


settings = Settings()
