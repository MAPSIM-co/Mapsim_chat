# app/db.py
import mysql.connector
from mysql.connector import Error
from app.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS

def get_connection():
    """
    بازگشت یک اتصال MySQL
    """
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME,
            charset="utf8mb4"
        )
        return conn
    except Error as e:
        raise RuntimeError(f"Can't connect to MySQL: {e}")