#!/usr/bin/env python3
import os
import shutil
import sqlite3

UPLOAD_DIR = "/root/Mapsim_chat/uploads"
DB_FILE = "/root/Mapsim_chat/chat.db"

def clear_uploads():
    print("🧹 Clearing uploads...")
    if not os.path.exists(UPLOAD_DIR):
        print("❌ uploads dir not found")
        return

    for name in os.listdir(UPLOAD_DIR):
        path = os.path.join(UPLOAD_DIR, name)
        try:
            if os.path.isfile(path) or os.path.islink(path):
                os.unlink(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
        except Exception as e:
            print(f"⚠️ Failed to delete {path}: {e}")

    print("✅ uploads cleared")

def clear_messages():
    print("🧹 Clearing messages table...")
    if not os.path.exists(DB_FILE):
        print("❌ DB not found")
        return

    try:
        conn = sqlite3.connect(DB_FILE, timeout=10)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages")
        conn.commit()
        conn.close()
        print("✅ messages table cleared")
    except Exception as e:
        print(f"❌ DB error: {e}")

if __name__ == "__main__":
    clear_uploads()
    clear_messages()