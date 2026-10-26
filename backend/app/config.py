from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    groq_api_key: str = ""
    model: str = "openai/gpt-oss-20b"
    database_url: str = "sqlite:///./planner.db"
    max_agent_steps: int = 8
    # Comma-separated list — add your Vercel URL here after deployment
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        return origins


settings = Settings()
