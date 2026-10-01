from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Configurações locais; segredos reais nunca devem possuir valor padrão."""

    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_prefix="NOXUS_",
        extra="ignore",
    )

    environment: str = "development"
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    data_file: Path = Path(".data/noxus.local.json")
    chat_provider: str = "disabled"
    crew_provider: str = "challenge3"
    crew_project: Path = BACKEND_ROOT.parent.parent / "challenge3" / "challenge3"
    crew_timeout_seconds: int = 600
    ingestion_api_key: SecretStr | None = None
    agent_project: Path = BACKEND_ROOT.parent.parent / "NOXUS-Agent-API-v2" / "noxus-local-v2"
    agent_api_url: str = "http://127.0.0.1:8000"

    @property
    def resolved_data_file(self) -> Path:
        # O arquivo antigo continha exemplos; fica preservado, mas não alimenta o painel.
        if self.data_file.name == "noxus.dev.json":
            return BACKEND_ROOT / ".data/noxus.local.json"
        if self.data_file.is_absolute():
            return self.data_file
        return BACKEND_ROOT / self.data_file

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
