#!/usr/bin/env python3
import os
import shutil
import sqlite3
import time

# --- تنظیمات ---
UPLOAD_DIR = "/root/Mapsim_chat/uploads"   # مسیر پوشه uploads
DB_FILE = "/root/Mapsim_chat/chat.db"      # مسیر دیتابیس SQLite
MAX_SIZE_GB = 3                          # حداکثر حجم پوشه به گیگابایت
CHECK_INTERVAL = 300                     # فاصله بررسی به ثانیه (مثلاً 300 = هر ۵ دقیقه)

# --- تابع محاسبه حجم پوشه ---
def get_folder_size(folder):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total_size += os.path.getsize(fp)
    return total_size / (1024 ** 3)  # تبدیل به گیگابایت

# --- پاک کردن فایل‌ها ---
def clear_uploads():
    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"خطا در حذف {file_path}: {e}")

# --- پاک کردن جدول پیام‌ها ---
def clear_messages():
    if not os.path.exists(DB_FILE):
        print("دیتابیس پیدا نشد!")
        return
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages")
        conn.commit()
        conn.close()
        print("جدول messages پاک شد.")
    except Exception as e:
        print(f"خطا در پاک کردن جدول messages: {e}")

# --- حلقه اصلی ---
if __name__ == "__main__":
    print("مانیتورینگ پوشه uploads شروع شد...")
    while True:
        size = get_folder_size(UPLOAD_DIR)
        if size >= MAX_SIZE_GB:
            print(f"حجم پوشه {size:.2f}GB است. پاکسازی شروع شد...")
            clear_uploads()
            clear_messages()
            print("پاکسازی انجام شد.")
        time.sleep(CHECK_INTERVAL)
