from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Pixel Cat Arena API"
    environment: str = "development"
    database_url: str | None = None
    cors_origins: list[str] = ["http://localhost:5173"]

    # Solana devnet prototype — Node helper scripts under solana_bridge/ do the actual
    # on-chain work; the treasury keypair never leaves the backend host.
    solana_bridge_dir: str = "solana_bridge"
    solana_treasury_keypair_path: str = "solana_bridge/treasury-keypair.json"
    solana_node_binary: str = "node"
    solana_metadata_base_url: str = "http://localhost:8000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
