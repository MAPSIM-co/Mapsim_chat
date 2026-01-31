# app/main.py
from fastapi import FastAPI, HTTPException, Form, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.security import OAuth2PasswordBearer
from app.create_db import create_database
from app.auth import register_user, authenticate_user, create_access_token, SECRET_KEY, ALGORITHM
from app.chat_keys import GLOBAL_CHAT_KEY
from jose import jwt, JWTError
import sqlite3
import os
import uuid
import shutil
from datetime import datetime
from app.websocket import router as chat_router

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "..", "chat.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "..", "uploads")
create_database()

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
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# ========= دریافت پیام‌های قبلی =========
@app.get("/messages/")
async def get_messages(token: str = Depends(oauth2_scheme), chat_id: str = "global"):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("username")
        if not username:
            raise HTTPException(status_code=403, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid token")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.id, u.username, m.type, m.content, m.timestamp
        FROM messages m
        JOIN users u ON m.user_id = u.id
        WHERE m.chat_id=?
        ORDER BY m.timestamp ASC
    """, (chat_id,))
    messages = [
        {"id": row[0], "username": row[1], "type": row[2], "text": row[3], "timestamp": row[4]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return {"messages": messages}

# ========= آپلود فایل =========
@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"file_url": f"/uploads/{filename}", "filename": file.filename}

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
    return {"key": GLOBAL_CHAT_KEY, "chat": "global"}
