import os
from pathlib import Path
from dotenv import load_dotenv
import platform

# مسیر پایه پروژه
BASE_DIR = Path(__file__).resolve().parent.parent

# لود فایل .env
load_dotenv(BASE_DIR / ".env")

# ======================
# تنظیمات دیتابیس MySQL
# ======================
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

if not all([DB_HOST, DB_NAME, DB_USER, DB_PASS]):
    raise RuntimeError("Database configuration is missing in .env")

# ======================
# مسیر آپلود فایل‌ها
# ======================
if platform.system() == "Darwin":  # macOS
    UPLOAD_DIR = str(BASE_DIR / "uploads")
else:  # VPS / Linux
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", str(BASE_DIR / "uploads"))

os.makedirs(UPLOAD_DIR, exist_ok=True)

# ======================
# تنظیمات JWT
# ======================
SECRET_KEY = os.getenv("SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set in .env")

# ======================
# حالت Debug
# ======================
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
