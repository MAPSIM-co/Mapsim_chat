# app/ws_secure_multidevice.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from jose import jwt, JWTError, ExpiredSignatureError
import json
import sqlite3
from app.config import DB_FILE
from app.auth import SECRET_KEY, ALGORITHM

router = APIRouter()
clients = {}  # chat_id -> { user_id -> [ws1, ws2, ...] }

def get_user_id(username: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username=?", (username,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return row[0]

def get_chat_id(chat_name: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM chats WHERE name=?", (chat_name,))
    row = cursor.fetchone()
    if not row:
        cursor.execute(
            "INSERT INTO chats(name, is_group) VALUES(?, ?)", (chat_name, 1)
        )
        conn.commit()
        chat_id = cursor.lastrowid
    else:
        chat_id = row[0]
    conn.close()
    return chat_id

def save_message(chat_id: int, user_id: int, type_: str, content: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages(chat_id, user_id, type, content) VALUES(?, ?, ?, ?)",
        (chat_id, user_id, type_, content)
    )
    conn.commit()
    conn.close()

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("username")
        user_id = payload.get("sub")
        if not username or not user_id:
            raise JWTError("Missing username or sub")
        return username, user_id
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: str = Query(...), chat_name: str = Query("global")):
    # 1️⃣ JWT verify
    try:
        username, user_id = verify_token(token)
    except HTTPException:
        await ws.close(code=4003)
        return

    # 2️⃣ chat_id
    chat_id = get_chat_id(chat_name)

    # 3️⃣ membership check
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM chat_members WHERE chat_id=? AND user_id=?", (chat_id, user_id)
    )
    is_member = cursor.fetchone()
    conn.close()
    if not is_member and chat_name != "global":
        await ws.close(code=4003)
        return

    # 4️⃣ accept connection
    await ws.accept()

    # 5️⃣ اضافه کردن ws به clients
    if chat_id not in clients:
        clients[chat_id] = {}
    if user_id not in clients[chat_id]:
        clients[chat_id][user_id] = []
    clients[chat_id][user_id].append(ws)

    try:
        while True:
            data = await ws.receive_text()
            payload = json.loads(data)
            msg_type = payload.get("type", "text")
            content = payload.get("text") or payload.get("file_path")

            # Save to DB
            save_message(chat_id, user_id, msg_type, content)

            # Broadcast پیام به همه کاربران chat
            for uid, ws_list in clients[chat_id].items():
                for client_ws in ws_list:
                    await client_ws.send_text(json.dumps({
                        "username": username,
                        "type": msg_type,
                        "text": content
                    }))

    except WebSocketDisconnect:
        # حذف فقط این ws
        clients[chat_id][user_id].remove(ws)
        if not clients[chat_id][user_id]:
            del clients[chat_id][user_id]
