# app/create_db.py
import mysql.connector
from mysql.connector import errorcode
from app.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

def create_database():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            charset='utf8mb4'
        )
        cursor = conn.cursor()

        # ایجاد دیتابیس اگر وجود نداشت
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;")
        cursor.execute(f"USE {DB_NAME};")

        # users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE,
            password VARCHAR(255) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # chats table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255),
            is_group TINYINT DEFAULT 0,
            is_private TINYINT DEFAULT 0
        )
        """)

        # chat_members table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_members (
            id INT AUTO_INCREMENT PRIMARY KEY,
            chat_id INT NOT NULL,
            user_id INT NOT NULL,
            FOREIGN KEY(chat_id) REFERENCES chats(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)

        # messages table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            chat_id INT NOT NULL,
            user_id INT NOT NULL,
            type VARCHAR(50) NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6),
            seen TINYINT DEFAULT 0,
            seen_at DATETIME NULL,
            deleted TINYINT DEFAULT 0,
            FOREIGN KEY(chat_id) REFERENCES chats(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)

        # files table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id VARCHAR(255) PRIMARY KEY,
            original_name VARCHAR(255) NOT NULL,
            mime_type VARCHAR(100) NOT NULL,
            enc_path VARCHAR(255) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # key_versions table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS key_versions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            enc_key BLOB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        print("✅ Database and tables are ready!")

    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("Something is wrong with your username or password")
        else:
            print(err)
    finally:
        cursor.close()
        conn.close()