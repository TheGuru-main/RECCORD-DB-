"""Backblaze B2 configuration (env-only)."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class B2Settings:
    key_id: str | None
    app_key: str | None
    bucket: str | None
    endpoint: str | None

    @property
    def enabled(self) -> bool:
        return bool(self.key_id and self.app_key and self.bucket and self.endpoint)


def get_b2_settings() -> B2Settings:
    return B2Settings(
        key_id=os.getenv("B2_KEY_ID") or None,
        app_key=os.getenv("B2_APP_KEY") or None,
        bucket=os.getenv("B2_BUCKET") or None,
        endpoint=os.getenv("B2_ENDPOINT") or None,
    )
