#!/usr/bin/env python3
import os
import shutil
from dotenv import load_dotenv
from app.db import get_connection

# ================= ENV =================
load_dotenv()

def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"[CLEAR_NOW] Missing env var: {name}")
    return value


UPLOAD_DIR = require_env("UPLOAD_DIR")

if not os.path.isdir(UPLOAD_DIR):
    raise RuntimeError(f"[CLEAR_NOW] UPLOAD_DIR does not exist: {UPLOAD_DIR}")

# ================= LOGIC =================
def clear_uploads():
    print("[CLEAR_NOW] Clearing uploads...")

    for name in os.listdir(UPLOAD_DIR):
        path = os.path.join(UPLOAD_DIR, name)
        try:
            if os.path.isfile(path) or os.path.islink(path):
                os.unlink(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
        except Exception as e:
            print(f"[CLEAR_NOW] Failed to delete {path}: {e}")

    print("[CLEAR_NOW] Uploads cleared")


def clear_messages():
    print("[CLEAR_NOW] Clearing messages table...")

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages")
        conn.commit()
        cursor.close()
        conn.close()
        print("[CLEAR_NOW] Messages Table cleared")
    except Exception as e:
        print(f"[CLEAR_NOW] DB error: {e}")


def clear_files():
    print("[CLEAR_NOW] Clearing files table...")

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM files")
        conn.commit()
        cursor.close()
        conn.close()
        print("[CLEAR_NOW] Files Table cleared")
    except Exception as e:
        print(f"[CLEAR_NOW] DB error: {e}")

def clear_KEY_version():
    print("[CLEAR_NOW] Clearing KEY Versions table...")

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM key_versions")
        conn.commit()
        cursor.close()
        conn.close()
        print("[CLEAR_NOW] KEY versions Table cleared")
    except Exception as e:
        print(f"[CLEAR_NOW] DB error: {e}")


if __name__ == "__main__":
    clear_uploads()
    clear_messages()
    clear_files()
    clear_KEY_version()
