from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Cấu hình đọc từ biến môi trường — không hard-code secret cho production."""

    app_env: str
    port: int
    secret_key: str
    app_version: str
    mongo_uri: str | None
    mongo_db_name: str


def load_settings() -> Settings:
    app_env = (os.getenv("APP_ENV") or "development").strip().lower()
    if app_env not in {"development", "production", "testing"}:
        app_env = "development"

    secret_key = os.getenv("SECRET_KEY")
    if app_env == "production" and not secret_key:
        raise RuntimeError("Biến SECRET_KEY là bắt buộc khi APP_ENV=production")

    if not secret_key:
        secret_key = "dev-only-insecure-key"

    mongo_uri = os.getenv("MONGO_URI")
    if mongo_uri is not None:
        mongo_uri = mongo_uri.strip() or None

    return Settings(
        app_env=app_env,
        port=int(os.getenv("PORT", "5000")),
        secret_key=secret_key,
        app_version=(os.getenv("APP_VERSION") or "0.1.0").strip(),
        mongo_uri=mongo_uri,
        mongo_db_name=(os.getenv("MONGO_DB_NAME") or "demo_db").strip(),
    )
