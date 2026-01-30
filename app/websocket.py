from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from jose import jwt, JWTError, ExpiredSignatureError
import json
import sqlite3
from app.config import DB_FILE
from app.auth import SECRET_KEY, ALGORITHM

router = APIRouter()

# ================== GLOBAL STATE ==================
clients = {}  # chat_id -> { user_id -> [ws1, ws2,...] }
online_users = {}  # user_id -> username

# ================== HELPERS ==================

def verify_token(token: str):
    """JWT verification"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("username")
        user_id = payload.get("sub")
        if not username or not user_id:
            raise JWTError
        return int(user_id), username
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def get_or_create_private_chat(user_ids: list):
    """نام chat خصوصی deterministic برای دو کاربر یا گروه"""
    sorted_ids = sorted(user_ids)
    chat_name = "private_" + "_".join(map(str, sorted_ids))
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM chats WHERE name=?", (chat_name,))
    row = cursor.fetchone()
    if row:
        chat_id = row[0]
    else:
        cursor.execute(
            "INSERT INTO chats(name, is_group, is_private) VALUES(?, ?, ?)",
            (chat_name, 0, 1)
        )
        chat_id = cursor.lastrowid
        # اضافه کردن اعضا
        for uid in user_ids:
            cursor.execute(
                "INSERT INTO chat_members(chat_id, user_id) VALUES(?, ?)",
                (chat_id, uid)
            )
        conn.commit()
    conn.close()
    return chat_id, chat_name

def check_membership(chat_id: int, user_id: int) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM chat_members WHERE chat_id=? AND user_id=?", (chat_id, user_id)
    )
    res = cursor.fetchone()
    conn.close()
    return bool(res)

def save_message(chat_id: int, user_id: int, msg_type: str, content: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages(chat_id, user_id, type, content) VALUES(?, ?, ?, ?)",
        (chat_id, user_id, msg_type, content)
    )
    conn.commit()
    conn.close()

async def broadcast_online_users():
    """ارسال لیست آنلاین‌ها به همه کاربران global"""
    data = {"type": "online_users", "users": list(online_users.values())}
    for ws_list in clients.get("global", {}).values():
        for ws in ws_list:
            await ws.send_text(json.dumps(data))

# ================== WEBSOCKET ==================

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: str = Query(...), chat_name: str = Query("global")):
    try:
        user_id, username = verify_token(token)
    except HTTPException:
        await ws.close(code=4003)
        return

    await ws.accept()

    # ثبت کاربر در online_users
    online_users[user_id] = username
    await broadcast_online_users()

    # تعیین chat_id
    if chat_name == "global":
        chat_id = "global"
    else:
        # برای چت خصوصی، باید user_id هم در اعضا باشد
        chat_id, chat_name = get_or_create_private_chat([user_id])  # در frontend user_ids دیگر هم باید ارسال شود

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

            # چک عضویت برای chat خصوصی
            if chat_name != "global" and not check_membership(chat_id, user_id):
                await ws.close(code=4003)
                return

            save_message(chat_id, user_id, msg_type, content)

            # ارسال پیام به همه اعضای chat
            for uid, ws_list in clients.get(chat_id, {}).items():
                for client_ws in ws_list:
                    await client_ws.send_text(json.dumps({
                        "username": username,
                        "type": msg_type,
                        "text": content,
                        "chat_name": chat_name
                    }))

    except WebSocketDisconnect:
        clients[chat_id][user_id].remove(ws)
        if not clients[chat_id][user_id]:
            del clients[chat_id][user_id]
        if user_id in online_users:
            del online_users[user_id]
        await broadcast_online_users()
