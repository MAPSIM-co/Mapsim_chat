#config.py

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# فقط روی مک یا لوکال لود میشه – روی VPS کاری نمی‌کنه
load_dotenv(BASE_DIR / ".env")

DB_FILE = os.getenv("DB_FILE", str(BASE_DIR / "chat.db"))
UPLOAD_DIR = os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads"))

SECRET_KEY = os.getenv("SECRET_KEY", "DEV_ONLY_CHANGE_ME_32_CHARS")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
)
