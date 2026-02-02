# app/main.py
from fastapi import FastAPI, HTTPException, Form, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer

from app.chat_keys import GLOBAL_CHAT_KEY
from jose import jwt, JWTError
from app.db import get_connection
import os
import uuid
import base64
from datetime import datetime

from nacl.secret import SecretBox
from fastapi.responses import StreamingResponse
import io

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "..", "uploads")

# -----------------------------
# 1️⃣ ساخت دیتابیس و جداول قبل از هر چیز
# -----------------------------
from app.create_db import create_database
create_database()

# ----------------------------
from app.chat_keys import GLOBAL_CHAT_KEY
from app.auth import register_user, authenticate_user, create_access_token, SECRET_KEY, ALGORITHM
from app.websocket import router as chat_router
# ----------------------------

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chat_router)

# Mount استاتیک و uploads
app.mount("/static", StaticFiles(directory="app/static"), name="static")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
#app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ========= دریافت پیام‌های قبلی =========

# ========= دریافت پیام‌های قبلی =========
@app.get("/messages/")
async def get_messages(token: str = Depends(oauth2_scheme), chat_id: str = "global"):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("username")
        user_id = payload.get("sub")
        if not username or not user_id:
            raise HTTPException(status_code=403, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid token")

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # --------- تبدیل chat_id به عدد ----------
            if chat_id.isdigit():
                real_chat_id = int(chat_id)
            else:
                cursor.execute("SELECT id FROM chats WHERE name=%s", (chat_id,))
                row = cursor.fetchone()
                if not row:
                    return {"messages": []}  # چت پیدا نشد
                real_chat_id = row[0]

            # --------- خواندن پیام‌ها ----------
            cursor.execute("""
                SELECT m.id, u.username, m.type, m.content, m.timestamp
                FROM messages m
                JOIN users u ON m.user_id = u.id
                WHERE m.chat_id=%s
                ORDER BY m.timestamp ASC
            """, (real_chat_id,))
            
            messages = [
                {"id": row[0], "username": row[1], "type": row[2], "text": row[3], "timestamp": row[4].strftime("%Y-%m-%d %H:%M:%S.%f")}
                for row in cursor.fetchall()
            ]
    finally:
        conn.close()

    return {"messages": messages}

# ========= آپلود فایل =========
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), token: str = Depends(oauth2_scheme)):
    """
    آپلود یک فایل و رمزنگاری آن با GLOBAL_CHAT_KEY
    ---
    پارامترها:
    - file: فایل آپلود شده
    - token: JWT احراز هویت
    """
    # 🔐 احراز هویت
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 👀 خواندن فایل
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")

    # 🔑 آماده کردن مسیر و شناسه فایل
    file_id = uuid.uuid4().hex
    enc_path = os.path.join(UPLOAD_DIR, f"{file_id}.enc")
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # 🔐 رمزنگاری با NaCl
    box = SecretBox(GLOBAL_CHAT_KEY)
    encrypted = box.encrypt(raw)

    # 💾 ذخیره فایل رمزنگاری شده روی دیسک
    with open(enc_path, "wb") as f:
        f.write(encrypted)

    # 🗄 ذخیره متادیتا در DB
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO files (id, original_name, mime_type, enc_path)
                VALUES (%s, %s, %s, %s)
            """, (file_id, file.filename, file.content_type, enc_path))
            conn.commit()
    finally:
        conn.close()

    # 🔗 بازگرداندن لینک دانلود فایل رمزگشایی شده
    return {
        "file_id": file_id,
        "file_url": f"/file/{file_id}"
}

# ========= ثبت نام =========
@app.post("/register/")
async def api_register(username: str = Form(...), password: str = Form(...), email: str = Form(None)):
    success, msg = register_user(username, password, email)
    if success:
        return {"message": msg}
    raise HTTPException(status_code=400, detail=msg)

# ========= ورود =========
@app.post("/login/")
async def api_login(username: str = Form(...), password: str = Form(...)):
    user_id = authenticate_user(username, password)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user_id), "username": username})
    return {"access_token": token}

# ========= کلید چت =========
@app.get("/chat/key")
async def get_global_chat_key(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401)

    return {
        "key": base64.b64encode(GLOBAL_CHAT_KEY).decode("utf-8"),
        "chat": "global"
    }

# ========= رمز گشایی فایل=========
@app.get("/file/{file_id}")
async def download_file(file_id: str, token: str = Depends(oauth2_scheme)):
    """
    دریافت و رمزگشایی فایل با GLOBAL_CHAT_KEY
    """
    # 🔐 احراز هویت
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 🗄 واکشی اطلاعات فایل از DB
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT original_name, mime_type, enc_path
                FROM files WHERE id=%s
            """, (file_id,))
            row = cursor.fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="File not found")

    original_name, mime_type, enc_path = row

    # 🔐 خواندن و رمزنگاری فایل
    try:
        with open(enc_path, "rb") as f:
            encrypted = f.read()
        box = SecretBox(GLOBAL_CHAT_KEY)
        decrypted = box.decrypt(encrypted)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to decrypt file")

    # 📤 بازگرداندن فایل به صورت StreamingResponse
    return StreamingResponse(
        io.BytesIO(decrypted),
        media_type=mime_type,
        headers={"Content-Disposition": f'inline; filename="{original_name}"'}
    )