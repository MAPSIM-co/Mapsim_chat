#!/usr/bin/env python3
import os
import shutil
import time
from dotenv import load_dotenv
from app.db import get_connection

# ================= ENV =================
load_dotenv()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"[AUTO_CLEAR] Missing required env var: {name}")
    return value


UPLOAD_DIR = require_env("UPLOAD_DIR")
MAX_SIZE_GB = float(require_env("UPLOAD_MAX_SIZE_GB"))
CHECK_INTERVAL = int(require_env("UPLOAD_CHECK_INTERVAL"))

if not os.path.isdir(UPLOAD_DIR):
    raise RuntimeError(f"[AUTO_CLEAR] UPLOAD_DIR does not exist: {UPLOAD_DIR}")

# ================= LOGIC =================
def get_folder_size_gb(folder: str) -> float:
    total_size = 0
    for dirpath, _, filenames in os.walk(folder):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total_size += os.path.getsize(fp)
    return total_size / (1024 ** 3)


def clear_uploads():
    for name in os.listdir(UPLOAD_DIR):
        path = os.path.join(UPLOAD_DIR, name)
        try:
            if os.path.isfile(path) or os.path.islink(path):
                os.unlink(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
        except Exception as e:
            print(f"[AUTO_CLEAR] Failed to remove {path}: {e}")


def clear_messages():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[AUTO_CLEAR] Failed to clear messages: {e}")

def clear_files():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM files")
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"[AUTO_CLEAR] Failed to clear files: {e}")


# ================= MAIN LOOP =================
if __name__ == "__main__":
    print("[AUTO_CLEAR] Service started")

    while True:
        try:
            size_gb = get_folder_size_gb(UPLOAD_DIR)
            print(f"[AUTO_CLEAR] Uploads size: {size_gb:.2f} GB")

            if size_gb >= MAX_SIZE_GB:
                print("[AUTO_CLEAR] Limit reached → clearing uploads & messages & Files")
                clear_uploads()
                clear_messages()
                clear_files()

        except Exception as e:
            print(f"[AUTO_CLEAR] Runtime error: {e}")

        time.sleep(CHECK_INTERVAL)
