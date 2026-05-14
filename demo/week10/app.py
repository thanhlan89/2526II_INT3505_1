from __future__ import annotations

import atexit
import logging
import signal
import sys
import time
import uuid
from typing import Any

from flask import Flask, g, jsonify, request

from config import Settings, load_settings
from logging_setup import configure_logging

logger = logging.getLogger(__name__)
access_logger = logging.getLogger("week10.access")
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
    configure_logging(settings)

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["APP_ENV"] = settings.app_env

    @app.before_request
    def _assign_request_id() -> None:
        raw = (request.headers.get("X-Request-ID") or "").strip()
        rid = raw if raw else str(uuid.uuid4())
        g.request_id = rid[:128]
        g._request_start = time.perf_counter()

    @app.after_request
    def _access_log_and_request_id_header(response):
        rid = getattr(g, "request_id", None)
        if rid:
            response.headers["X-Request-ID"] = rid
        start = getattr(g, "_request_start", None)
        duration_ms = (
            (time.perf_counter() - start) * 1000.0 if start is not None else None
        )
        access_logger.info(
            "http_access",
            extra={
                "request_id": rid,
                "http_method": request.method,
                "url_path": request.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 3) if duration_ms is not None else None,
            },
        )
        return response

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
    s = load_settings()
    app.run(host="0.0.0.0", port=s.port, debug=s.app_env == "development")
