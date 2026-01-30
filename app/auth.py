# app/auth.py

import sqlite3
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from app.create_db import DB_FILE
import platform

SECRET_KEY = "CHANGE_THIS_SECRET_LATER"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# ⚡ انتخاب scheme بر اساس OS
if platform.system() == "Darwin":  # macOS
    pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
else:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def register_user(username, password, email):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username=? OR email=?", (username, email))
    if cursor.fetchone():
        conn.close()
        return False, "Username or email exists"

    hashed = hash_password(password)
    cursor.execute(
        "INSERT INTO users(username, email, password) VALUES(?, ?, ?)",
        (username, email, hashed)
    )
    conn.commit()
    conn.close()
    return True, "Registered"

def authenticate_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, password FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    user_id, hashed = row
    if verify_password(password, hashed):
        return user_id
    return None
