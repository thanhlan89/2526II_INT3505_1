from __future__ import annotations

import atexit
import logging
import signal
import sys
from typing import Any

from flask import Flask, jsonify

from config import Settings, load_settings

logger = logging.getLogger(__name__)
_shutdown_hooks_registered = False


def _close_mongo_client(client: Any) -> None:
    if client is not None:
        try:
            client.close()
        except Exception as exc:  # noqa: BLE001 — shutdown: ghi log và bỏ qua
            logger.warning("Đóng Mongo client lỗi: %s", exc)


def _register_signals(client: Any) -> None:
    global _shutdown_hooks_registered
    if _shutdown_hooks_registered:
        return
    _shutdown_hooks_registered = True

    def _shutdown(_signum: int | None = None, _frame: Any | None = None) -> None:
        _close_mongo_client(client)
        sys.exit(0)

    atexit.register(_close_mongo_client, client)
    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)


def create_app(settings: Settings | None = None) -> Flask:
    settings = settings or load_settings()
    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["APP_ENV"] = settings.app_env

    mongo_client: Any = None
    if settings.mongo_uri:
        from pymongo import MongoClient

        mongo_client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=2000)
        app.extensions["mongo_client"] = mongo_client
        app.extensions["mongo_db"] = mongo_client[settings.mongo_db_name]

    _register_signals(mongo_client)

    @app.get("/health")
    def health():
        """Liveness: process còn phục vụ request."""
        return (
            jsonify(
                {
                    "status": "ok",
                    "version": settings.app_version,
                    "env": settings.app_env,
                }
            ),
            200,
        )

    @app.get("/ready")
    def ready():
        """Readiness: kiểm tra dependency (Mongo) nếu được cấu hình."""
        checks: dict[str, str] = {}
        if settings.mongo_uri:
            client = app.extensions.get("mongo_client")
            if client is None:
                checks["database"] = "error: client missing"
                return jsonify({"status": "not_ready", "checks": checks}), 503
            try:
                client.admin.command("ping")
                checks["database"] = "ok"
            except Exception as exc:  # noqa: BLE001
                checks["database"] = f"error: {exc!s}"
                return jsonify({"status": "not_ready", "checks": checks}), 503
        else:
            checks["database"] = "skipped (MONGO_URI unset)"

        return jsonify({"status": "ready", "checks": checks}), 200

    @app.get("/")
    def root():
        return jsonify({"service": "week10", "docs": "/health, /ready"}), 200

    return app


app = create_app()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    s = load_settings()
    app.run(host="0.0.0.0", port=s.port, debug=s.app_env == "development")
