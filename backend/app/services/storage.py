from __future__ import annotations

import mimetypes
import os
import secrets
from pathlib import Path
from urllib.parse import urlparse

from fastapi import HTTPException

from app.config import settings


class MediaStorage:
    def save(self, data: bytes, content_type: str, extension: str) -> tuple[str, str]:
        raise NotImplementedError

    def delete(self, object_key: str) -> None:
        raise NotImplementedError


class LocalMediaStorage(MediaStorage):
    def __init__(self) -> None:
        self.root = Path(settings.media_dir).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, data: bytes, content_type: str, extension: str) -> tuple[str, str]:
        filename = f"{secrets.token_urlsafe(18)}.{extension}"
        path = self.root / filename
        path.write_bytes(data)
        return filename, filename

    def delete(self, object_key: str) -> None:
        safe_name = Path(object_key).name
        path = self.root / safe_name
        try:
            path.unlink()
        except FileNotFoundError:
            pass


class S3MediaStorage(MediaStorage):
    def __init__(self) -> None:
        try:
            import boto3  # type: ignore
        except ImportError as exc:
            raise RuntimeError("boto3 is required when STORAGE_PROVIDER=s3") from exc
        self._client = boto3.client(
            "s3",
            region_name=settings.s3_region or None,
            endpoint_url=settings.s3_endpoint_url or None,
            aws_access_key_id=settings.s3_access_key_id or None,
            aws_secret_access_key=settings.s3_secret_access_key or None,
        )
        if not settings.s3_bucket:
            raise RuntimeError("S3_BUCKET is required when STORAGE_PROVIDER=s3")

    def save(self, data: bytes, content_type: str, extension: str) -> tuple[str, str]:
        import io
        key = f"listing-images/{secrets.token_urlsafe(18)}.{extension}"
        self._client.upload_fileobj(
            io.BytesIO(data),
            settings.s3_bucket,
            key,
            ExtraArgs={"ContentType": content_type, "CacheControl": "public, max-age=31536000, immutable"},
        )
        return key, self._public_url(key)

    def _public_url(self, key: str) -> str:
        if settings.s3_public_base_url:
            return f"{settings.s3_public_base_url.rstrip('/')}/{key}"
        if settings.s3_endpoint_url:
            return f"{settings.s3_endpoint_url.rstrip('/')}/{settings.s3_bucket}/{key}"
        region = settings.s3_region or "us-east-1"
        host = f"{settings.s3_bucket}.s3.{region}.amazonaws.com"
        return f"https://{host}/{key}"

    def delete(self, object_key: str) -> None:
        if object_key.startswith("http"):
            object_key = urlparse(object_key).path.lstrip("/")
            prefix = f"{settings.s3_bucket}/"
            if object_key.startswith(prefix):
                object_key = object_key[len(prefix):]
        self._client.delete_object(Bucket=settings.s3_bucket, Key=object_key)


def get_storage() -> MediaStorage:
    if settings.storage_provider.lower() == "s3":
        return S3MediaStorage()
    return LocalMediaStorage()


def object_key_from_url(url: str) -> str | None:
    if not url:
        return None
    if settings.storage_provider.lower() != "s3":
        return Path(urlparse(url).path).name
    parsed = urlparse(url)
    key = parsed.path.lstrip("/")
    prefix = f"{settings.s3_bucket}/"
    if key.startswith(prefix):
        key = key[len(prefix):]
    return key or None


def delete_media_url(url: str) -> None:
    key = object_key_from_url(url)
    if not key:
        return
    try:
        get_storage().delete(key)
    except Exception:
        # Media deletion must not make a valid database transaction fail.
        return
