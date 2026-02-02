# app/auth.py

from app.db import get_connection
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
import platform

SECRET_KEY = "CHANGE_THIS_SECRET_LATER"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# ⚡ انتخاب scheme بر اساس OS
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)


def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def register_user(username, password, email=None):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:

            # اگر ایمیل داده شده
            if email:
                cursor.execute(
                    "SELECT id FROM users WHERE username=%s OR email=%s",
                    (username, email)
                )
            else:
                cursor.execute(
                    "SELECT id FROM users WHERE username=%s",
                    (username,)
                )

            if cursor.fetchone():
                return False, "Username or email exists"

            hashed = hash_password(password)

            # 🔑 اگر ایمیل خالی است، None (NULL) ذخیره کن
            email_value = email if email else None

            cursor.execute(
                "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)",
                (username, email_value, hashed)
            )
            conn.commit()

    finally:
        conn.close()

    return True, "Registered"



def authenticate_user(username, password):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, password FROM users WHERE username=%s", (username,))
            row = cursor.fetchone()
    finally:
        conn.close()

    if not row:
        return None

    user_id, hashed = row
    if verify_password(password, hashed):
        return user_id
    return None