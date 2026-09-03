from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from alembic import command
from alembic.config import Config
from app.config import get_settings


@pytest.fixture(scope="session", autouse=True)
def _migrate_schema():
    ini = Path(__file__).resolve().parents[2] / "alembic.ini"
    command.upgrade(Config(str(ini)), "head")


@pytest.fixture(scope="session")
def settings():
    return get_settings()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("STORAGE_DIR", str(tmp_path / "storage"))
    get_settings.cache_clear()
    from app.main import app

    return TestClient(app)


@pytest.fixture()
def assets_dir() -> Path:
    return Path(__file__).resolve().parents[3] / "data" / "assets"
