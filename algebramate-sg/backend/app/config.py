from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AlgebraMate SG"
    database_url: str = "sqlite:///./data/algebra_tutor.db"
    chroma_path: str = "./data/chroma"
    jwt_secret: str = "change-me-for-local-development"
    jwt_expire_minutes: int = 1440
    agent_router_api_key: str | None = None
    agent_router_base_url: str | None = None
    primary_model: str = "gpt-5.6-sol"
    fast_model: str = "deepseek-v4-flash"
    embedding_provider: str = "local"
    embedding_model: str = "all-MiniLM-L6-v2"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def data_dir(self) -> Path:
        path = Path(self.chroma_path).parent
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
