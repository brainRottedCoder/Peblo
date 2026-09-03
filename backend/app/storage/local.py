from __future__ import annotations

import os
from pathlib import Path


class LocalDiskStorage:
    def __init__(self, root: Path, public_base_url: str) -> None:
        self.root = Path(root)
        self.public_base_url = public_base_url.rstrip("/")
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        if ".." in Path(key).parts:
            raise ValueError("Invalid storage key")
        return self.root / key

    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key

    def put_atomic(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Write via a sibling .tmp then os.replace — readers never see a partial file."""
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
        return key

    def get(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path(key).is_file()

    def url(self, key: str) -> str:
        return f"{self.public_base_url}/media/{key}"

    def healthcheck(self) -> None:
        probe = self.root / ".health"
        probe.write_bytes(b"ok")
        probe.unlink(missing_ok=True)
