# app/chat_keys.py
import os
import base64
from nacl.secret import SecretBox
from app.db import get_connection

# -----------------------------
# MASTER_KEY باید در env باشد
# -----------------------------
MASTER_KEY_B64 = os.environ.get("SECRET_KEY")
if not MASTER_KEY_B64:
    raise RuntimeError("SECRET_KEY is not set")
MASTER_KEY = base64.b64decode(MASTER_KEY_B64)

# -----------------------------
# ایجاد جدول key_versions اگر وجود ندارد
# -----------------------------
with get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS key_versions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            enc_key LONGBLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        conn.commit()

# -----------------------------
# تولید GLOBAL_KEY جدید (runtime)
# -----------------------------
def generate_global_key() -> bytes:
    """یک کلید 32 بایتی تصادفی بساز"""
    return os.urandom(32)

# -----------------------------
# ذخیره GLOBAL_KEY رمزگذاری شده
# -----------------------------
def store_key_version(global_key: bytes) -> int:
    """GLOBAL_KEY را رمزگذاری و در جدول ثبت می‌کند"""
    box = SecretBox(MASTER_KEY)
    enc = box.encrypt(global_key)
    enc_bytes = bytes(enc)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO key_versions(enc_key) VALUES (%s)",
                (enc_bytes,)
            )
            conn.commit()  # مطمئن شو commit واقعی انجام می‌شود
            return cursor.lastrowid

# -----------------------------
# بارگذاری آخرین GLOBAL_KEY
# -----------------------------
def load_latest_global_key() -> bytes:
    """آخرین GLOBAL_KEY ذخیره شده را از جدول می‌خواند"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT enc_key FROM key_versions ORDER BY id DESC LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                enc_key = row[0]
                box = SecretBox(MASTER_KEY)
                return box.decrypt(enc_key)
    return None

# -----------------------------
# GLOBAL_KEY runtime جدید برای کاربران
# -----------------------------
# همیشه یک کلید جدید بساز (برای هر ریست سرور)
GLOBAL_CHAT_KEY = generate_global_key()

# ذخیره GLOBAL_KEY جدید در key_versions
new_key_id = store_key_version(GLOBAL_CHAT_KEY)

# -----------------------------
# محافظ حرفه‌ای
# -----------------------------
assert isinstance(GLOBAL_CHAT_KEY, (bytes, bytearray))
assert len(GLOBAL_CHAT_KEY) == 32

print(f"✅ GLOBAL_CHAT_KEY generated and stored (id={new_key_id}) for this session")
