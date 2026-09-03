from __future__ import annotations

from typing import Protocol


class StorageBackend(Protocol):
    """Swap local disk for Cloudflare R2 by implementing this protocol.

    To move to R2: set STORAGE_BACKEND=r2 and the R2_* env vars. No call sites change.
    """

    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str: ...

    def put_atomic(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str: ...

    def get(self, key: str) -> bytes: ...

    def exists(self, key: str) -> bool: ...

    def url(self, key: str) -> str: ...

    def healthcheck(self) -> None: ...
