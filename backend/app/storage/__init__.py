from app.config import get_settings
from app.storage.base import StorageBackend
from app.storage.local import LocalDiskStorage
from app.storage.r2 import R2Storage


def get_storage() -> StorageBackend:
    settings = get_settings()
    if settings.storage_backend == "r2":
        return R2Storage(settings)
    return LocalDiskStorage(settings.storage_dir, settings.public_base_url)
