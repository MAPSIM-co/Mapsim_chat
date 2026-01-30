#!/usr/bin/env python3
import os
import shutil
import sqlite3
import time

UPLOAD_DIR = "/root/Mapsim_chat/uploads"   # مسیر پوشه uploads
DB_FILE = "/root/Mapsim_chat/chat.db"      # مسیر دیتابیس SQLite
MAX_SIZE_GB = 3                          # حداکثر حجم پوشه
CHECK_INTERVAL = 14400                    # هر ۴ ساعت = 4*60*60 ثانیه

def get_folder_size(folder):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total_size += os.path.getsize(fp)
    return total_size / (1024 ** 3)

def clear_uploads():
    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except:
            pass  # کاملاً بدون پیام خطا

def clear_messages():
    if not os.path.exists(DB_FILE):
        return
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages")
        conn.commit()
        conn.close()
    except:
        pass  # کاملاً بدون پیام خطا

if __name__ == "__main__":
    while True:
        size = get_folder_size(UPLOAD_DIR)
        if size >= MAX_SIZE_GB:
            clear_uploads()
            clear_messages()
        time.sleep(CHECK_INTERVAL)
