"""Backblaze B2 storage client (S3-compatible)."""

from __future__ import annotations

import json
import logging
from typing import Any

from app.core.b2_config import get_b2_settings

logger = logging.getLogger(__name__)


class B2Service:
    def __init__(self) -> None:
        self.settings = get_b2_settings()
        self._client = None

    @property
    def enabled(self) -> bool:
        return self.settings.enabled

    def _get_client(self):
        if not self.enabled:
            return None
        if self._client is not None:
            return self._client
        try:
            import boto3
            from botocore.config import Config

            self._client = boto3.client(
                "s3",
                endpoint_url=self.settings.endpoint,
                aws_access_key_id=self.settings.key_id,
                aws_secret_access_key=self.settings.app_key,
                config=Config(signature_version="s3v4"),
            )
            return self._client
        except Exception as exc:
            logger.warning("B2 client init failed: %s", exc)
            return None

    def put_json(self, key: str, data: dict[str, Any]) -> bool:
        body = json.dumps(data, default=str).encode("utf-8")
        return self.put_bytes(key, body, content_type="application/json")

    def put_bytes(
        self,
        key: str,
        body: bytes,
        content_type: str = "application/octet-stream",
    ) -> bool:
        client = self._get_client()
        if client is None:
            logger.info("B2 disabled; skip put %s", key)
            return False
        try:
            client.put_object(
                Bucket=self.settings.bucket,
                Key=key,
                Body=body,
                ContentType=content_type,
            )
            return True
        except Exception as exc:
            logger.exception("B2 put failed for %s: %s", key, exc)
            return False

    def get_json(self, key: str) -> dict[str, Any] | None:
        client = self._get_client()
        if client is None:
            return None
        try:
            resp = client.get_object(
                Bucket=self.settings.bucket,
                Key=key,
            )
            raw = resp["Body"].read()
            return json.loads(raw.decode("utf-8"))
        except Exception as exc:
            # NoSuchKey and other misses
            logger.debug("B2 get miss/fail for %s: %s", key, exc)
            return None


b2_service = B2Service()
