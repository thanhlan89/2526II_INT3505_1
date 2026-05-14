from __future__ import annotations

import logging
import sys
from config import Settings


def configure_logging(settings: Settings) -> None:
    """Thiết lập logging: JSON trên stdout (production) hoặc dòng text (development)."""
    root = logging.getLogger()
    root.handlers.clear()

    level_name = settings.log_level.upper()
    level = getattr(logging, level_name, logging.INFO)
    root.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    if settings.log_json:
        from pythonjsonlogger import jsonlogger

        fmt: logging.Formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    else:
        fmt = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    handler.setFormatter(fmt)
    root.addHandler(handler)

    # Giảm ồn từ thư viện (tuỳ chọn)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
