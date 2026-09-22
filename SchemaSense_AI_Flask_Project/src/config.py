from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_chat_model: str = "gpt-5-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    pinecone_api_key: str = ""
    pinecone_index_name: str = "schemasense-metadata"
    pinecone_namespace: str = "synthetic-v1"
    pinecone_cloud: str = "aws"
    pinecone_region: str = "us-east-1"
    retrieval_top_k: int = Field(default=5, ge=1, le=10)
    retrieval_min_score: float = Field(default=0.20, ge=0.0, le=1.0)
    max_tool_calls: int = Field(default=4, ge=1, le=8)
    max_er_tables: int = Field(default=12, ge=2, le=20)
    metadata_path: Path = PROJECT_ROOT / "data" / "synthetic_metadata.json"

    def require_runtime_keys(self) -> None:
        missing = []
        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        if not self.pinecone_api_key:
            missing.append("PINECONE_API_KEY")
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


@lru_cache
def get_settings() -> Settings:
    return Settings()

