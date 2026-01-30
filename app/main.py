# app/main.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Form, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.create_db import create_database
from app.auth import register_user, authenticate_user , create_access_token , SECRET_KEY , ALGORITHM
from datetime import datetime
from jose import jwt, JWTError
import sqlite3
import os
import uuid
import shutil




#DB_FILE = "chat.db"
#UPLOAD_DIR = "uploads"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "..", "chat.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "..", "uploads")


create_database()

app = FastAPI()

# دریافت پیام‌های قبلی (پایداری چت)
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

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
        {
            "id": row[0],
            "username": row[1],
            "type": row[2],
            "text": row[3],
            "timestamp": row[4]
        }
        for row in cursor.fetchall()
    ]
    conn.close()
    return {"messages": messages}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

connections = {}









@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    # ابتدا JWT را بررسی می‌کنیم
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        #print("[WebSocket] JWT payload:", payload)
        username = payload.get("username")
        if not username:
            #print("[WebSocket] JWT payload missing 'username'.")
            await websocket.close(code=4003)
            return
    except JWTError as e:
        print("[WebSocket] JWTError:", e)
        await websocket.close(code=4003)
        return

    # پس از تایید JWT، کانکشن را قبول می‌کنیم
    await websocket.accept()

    chat_id = "global"
    if chat_id not in connections:
        connections[chat_id] = []
    connections[chat_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "text")
            content = data.get("text", "")

            timestamp = save_message(chat_id, username, msg_type, content)

            for conn in connections[chat_id]:
                await conn.send_json({
                    "username": username,
                    "type": msg_type,
                    "text": content,
                    "timestamp": timestamp
                })
    except WebSocketDisconnect:
        connections[chat_id].remove(websocket)


def save_message(chat_id, username, msg_type, content):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE username=?", (username,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users(username, password) VALUES(?, ?)", (username, ""))
        conn.commit()
        user_id = cursor.lastrowid
    else:
        user_id = user[0]

    timestamp = datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO messages(chat_id, user_id, type, content, timestamp) VALUES(?, ?, ?, ?, ?)",
        (chat_id, user_id, msg_type, content, timestamp)
    )
    conn.commit()
    conn.close()
    return timestamp

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"file_url": f"/uploads/{filename}", "filename": file.filename}

@app.post("/register/")
async def api_register(
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(None)
):
    success, msg = register_user(username, password, email)
    if success:
        return {"message": msg}
    else:
        raise HTTPException(status_code=400, detail=msg)



@app.post("/login/")
async def api_login(username: str = Form(...), password: str = Form(...)):
    user_id = authenticate_user(username, password)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user_id), "username": username})
    return {"access_token": token}
