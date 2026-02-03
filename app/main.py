# app/main.py
from fastapi import FastAPI, HTTPException, Form, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer

from app.chat_keys import GLOBAL_CHAT_KEY
from jose import jwt, JWTError
from app.db import get_connection
import os
import sys
import uuid
import base64
from datetime import datetime
from dotenv import load_dotenv
from nacl.secret import SecretBox
from fastapi.responses import StreamingResponse
import io

# -----------------------------
# Load .env
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if getattr(sys, 'frozen', False):
    # حالت PyInstaller باینری
    base_dir = sys._MEIPASS
    env_path = os.path.join(os.path.dirname(sys.executable), ".env")
else:
    base_dir = BASE_DIR
    env_path = os.path.join(BASE_DIR, "..", ".env")

load_dotenv(env_path)

# -----------------------------
# مسیر static
# -----------------------------
if getattr(sys, 'frozen', False):
    static_path = os.path.join(sys._MEIPASS, "app", "static")
else:
    static_path = os.path.join(BASE_DIR, "static")

# -----------------------------
# مسیر uploads
# -----------------------------
UPLOAD_DIR = os.path.join(BASE_DIR, "..", "uploads")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# -----------------------------
# 1️⃣ ساخت دیتابیس و جداول قبل از هر چیز
# -----------------------------
from app.create_db import create_database
create_database()

# -----------------------------
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

# Routers
app.include_router(chat_router)

# Mount static
app.mount("/static", StaticFiles(directory=static_path), name="static")
# دایرکتوری uploads را فقط بساز
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

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
            if chat_id.isdigit():
                real_chat_id = int(chat_id)
            else:
                cursor.execute("SELECT id FROM chats WHERE name=%s", (chat_id,))
                row = cursor.fetchone()
                if not row:
                    return {"messages": []}
                real_chat_id = row[0]

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
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")

    file_id = uuid.uuid4().hex
    enc_path = os.path.join(UPLOAD_DIR, f"{file_id}.enc")
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    box = SecretBox(GLOBAL_CHAT_KEY)
    encrypted = box.encrypt(raw)

    with open(enc_path, "wb") as f:
        f.write(encrypted)

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
    try:
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")

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

    try:
        with open(enc_path, "rb") as f:
            encrypted = f.read()
        box = SecretBox(GLOBAL_CHAT_KEY)
        decrypted = box.decrypt(encrypted)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to decrypt file")

    return StreamingResponse(
        io.BytesIO(decrypted),
        media_type=mime_type,
        headers={"Content-Disposition": f'inline; filename="{original_name}"'}
    )