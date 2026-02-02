#!/usr/bin/env python3


############################################################################
#                                                                          #
#               RUN Command : sudo python3 reset_database.py.              #
#                                                                          #
############################################################################


import mysql.connector
from mysql.connector import Error
import sys

DB_NAME = "chatdb"

def main():
    try:
        # ⚡ اتصال به MySQL با کاربر root (بدون پسورد، باید sudo باشد)
        conn = mysql.connector.connect(
            host="localhost",
            user="root"
        )
        cursor = conn.cursor()
        print(f"[RESET_DB] Connected to MySQL as root ✅")

        # ⚡ حذف دیتابیس اگر وجود داشت
        cursor.execute(f"DROP DATABASE IF EXISTS {DB_NAME}")
        print(f"[RESET_DB] Database {DB_NAME} dropped ✅")

        # ⚡ ایجاد دوباره دیتابیس با utf8mb4
        cursor.execute(f"CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"[RESET_DB] Database {DB_NAME} created ✅")

        cursor.close()
        conn.close()
        print("[RESET_DB] Done! You can now start your server and tables will be auto-created.")
    except mysql.connector.Error as e:
        print(f"[RESET_DB] MySQL Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
