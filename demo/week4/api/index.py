from pathlib import Path
import sys

# Cho phép import app.py ở thư mục cha khi chạy trên Vercel.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import app  # noqa: E402

