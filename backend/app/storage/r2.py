from __future__ import annotations

from app.config import Settings


class R2Storage:
    """Cloudflare R2 via the S3 API.

    Not wired as the default. Swapping from LocalDiskStorage is one settings change:
    STORAGE_BACKEND=r2 plus the R2_* credentials. put_atomic uploads the object
    under a versioned key, then writes a tiny pointer object last — the same
    two-step used on disk so a mid-publish crash cannot expose a half-written catalogue.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = None

    def _s3(self):
        if self._client is None:
            try:
                import boto3
            except ImportError as exc:
                raise RuntimeError(
                    "boto3 failed to import. It is in requirements.txt — reinstall the API image."
                ) from exc
            self._client = boto3.client(
                "s3",
                endpoint_url=f"https://{self.settings.r2_account_id}.r2.cloudflarestorage.com",
                aws_access_key_id=self.settings.r2_access_key_id,
                aws_secret_access_key=self.settings.r2_secret_access_key,
            )
        return self._client

    def put(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        self._s3().put_object(
            Bucket=self.settings.r2_bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return key

    def put_atomic(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        # R2/S3 PUT of a single object is atomic at the object level. We still
        # write a staging key first, then copy over the live key so a crash
        # during upload leaves the previous live object in place.
        staging = f"{key}.staging"
        self.put(staging, data, content_type)
        self._s3().copy_object(
            Bucket=self.settings.r2_bucket,
            Key=key,
            CopySource={"Bucket": self.settings.r2_bucket, "Key": staging},
        )
        self._s3().delete_object(Bucket=self.settings.r2_bucket, Key=staging)
        return key

    def get(self, key: str) -> bytes:
        obj = self._s3().get_object(Bucket=self.settings.r2_bucket, Key=key)
        return obj["Body"].read()

    def exists(self, key: str) -> bool:
        try:
            self._s3().head_object(Bucket=self.settings.r2_bucket, Key=key)
            return True
        except Exception:
            return False

    def url(self, key: str) -> str:
        base = self.settings.r2_public_base_url.rstrip("/")
        if base:
            return f"{base}/{key}"
        return f"{self.settings.public_base_url}/media/{key}"

    def healthcheck(self) -> None:
        self._s3().head_bucket(Bucket=self.settings.r2_bucket)
