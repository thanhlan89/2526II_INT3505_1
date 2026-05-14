"""Entry point cho Gunicorn: gunicorn -w 2 -b 0.0.0.0:5000 wsgi:app"""

from app import app

__all__ = ["app"]
