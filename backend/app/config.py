from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/config.py → repo root is parents[2]
REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Peblo TV Mini"
    env: str = "dev"
    secret_key: str = "change-me-in-production"
    jwt_expire_minutes: int = 12 * 60
    database_url: str = "postgresql+psycopg://peblo:peblo@localhost:5432/peblo"
    storage_backend: str = "local"  # local | r2
    storage_dir: Path = REPO_ROOT / "data" / "storage"
    data_dir: Path = REPO_ROOT / "data"
    public_base_url: str = "http://localhost:8000"
    cors_origins: str = "http://localhost:5173,http://localhost:5174,http://localhost:3000"

    # Cloudflare R2 (unused unless STORAGE_BACKEND=r2)
    r2_account_id: str = ""
    r2_access_key_id: str = ""
    r2_secret_access_key: str = ""
    r2_bucket: str = "peblo-tv"
    r2_public_base_url: str = ""

    seed_admin_email: str = "admin@peblo.local"
    seed_admin_password: str = "admin-password"
    seed_editor_email: str = "editor@peblo.local"
    seed_editor_password: str = "editor-password"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
