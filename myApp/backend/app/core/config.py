from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "Proximity API"
    app_env: str = "dev"
    app_debug: bool = True

    api_v1_prefix: str = "/api/v1"

    secret_key: str = "change-me"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"
    admin_api_key: str = "change-me-admin-key"

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/proximity"

    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:8081", "http://127.0.0.1:8081"]
    )

    # Actian / VectorAI (external vector DB)
    vectorai_enabled: bool = False
    vectorai_address: str = "127.0.0.1:50051"
    vectorai_api_key: str | None = None
    vectorai_collection_name: str = "user_profiles_embed_v1"
    vectorai_metric: str = "COSINE"
    vectorai_dimension: int | None = None
    vectorai_supports_metadata_filtering: bool = False
    vectorai_batch_upsert_size: int = 100
    vectorai_request_timeout_seconds: float | None = None
    vectorai_probe_metadata_filtering_on_startup: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
