# app/websocket.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from jose import jwt, JWTError, ExpiredSignatureError
import json
from app.db import get_connection
from app.auth import SECRET_KEY, ALGORITHM
from datetime import datetime, timezone

router = APIRouter()

# ================== GLOBAL STATE ==================
clients = {}       # chat_id -> { user_id -> [ws1, ws2,...] }
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
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM chats WHERE name=%s", (chat_name,))
            row = cursor.fetchone()
            if row:
                chat_id = row[0]
            else:
                cursor.execute(
                    "INSERT INTO chats(name, is_group, is_private) VALUES(%s, %s, %s)",
                    (chat_name, 0, 1)
                )
                chat_id = cursor.lastrowid
                for uid in user_ids:
                    cursor.execute(
                        "INSERT INTO chat_members(chat_id, user_id) VALUES(%s, %s)",
                        (chat_id, uid)
                    )
                conn.commit()
    finally:
        conn.close()
    return chat_id, chat_name

def check_membership(chat_id: int, user_id: int) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM chat_members WHERE chat_id=%s AND user_id=%s", (chat_id, user_id)
            )
            res = cursor.fetchone()
    finally:
        conn.close()
    return bool(res)

def save_message(chat_id: int, user_id: int, msg_type: str, content: str, ts: str):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO messages(chat_id, user_id, type, content, timestamp)
                VALUES(%s, %s, %s, %s, %s)
                """,
                (chat_id, user_id, msg_type, content, ts)
            )
            conn.commit()
    finally:
        conn.close()

# ================== BROADCAST ==================
async def broadcast_online_users(exclude_ws=None):
    data = {"type": "online_users", "users": list(online_users.values())}
    
    ws_lists = clients.get("global", {}).values()
    
    for ws_list in ws_lists:
        for ws in ws_list.copy():
            if ws == exclude_ws:
                continue
            try:
                await ws.send_text(json.dumps(data))
            except RuntimeError:
                # حذف ws قطع شده
                ws_list.remove(ws)

async def broadcast_message(chat_id, payload):
    if chat_id not in clients:
        return
    for ws_list in clients[chat_id].values():
        for ws in ws_list.copy():
            try:
                await ws.send_text(json.dumps(payload))
            except RuntimeError:
                ws_list.remove(ws)

# ================== WEBSOCKET ==================

@router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, token: str = Query(...), chat_name: str = Query("global")):
    try:
        user_id, username = verify_token(token)
    except Exception:
        await ws.close(code=4003)
        return

    await ws.accept()

    # ثبت کاربر آنلاین
    online_users[user_id] = username

    # ارسال آنلاین‌ها به خودش
    await ws.send_text(json.dumps({
        "type": "online_users",
        "users": list(online_users.values())
    }))
    # اطلاع به دیگران
    await broadcast_online_users(exclude_ws=ws)

    # تعیین chat_id
    
    if chat_name == "global":
        # اتصال به دیتابیس
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM chats WHERE name='global'")
                row = cursor.fetchone()
                if row:
                    chat_id = row[0]
                else:
                    cursor.execute(
                        "INSERT INTO chats(name, is_group, is_private) VALUES(%s, %s, %s)",
                        ("global", 0, 0)
                    )
                    chat_id = cursor.lastrowid
                    conn.commit()
        finally:
            conn.close()
    else:
        chat_id, chat_name = get_or_create_private_chat([user_id])

    # ثبت ws در clients
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

            if chat_name != "global" and not check_membership(chat_id, user_id):
                await ws.close(code=4003)
                return

            ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")
            

            
            save_message(chat_id, user_id, msg_type, content, ts)

            msg_payload = {
                "username": username,
                "type": msg_type,
                "text": content,
                "chat_name": chat_name,
                "timestamp": ts
            }

            await broadcast_message(chat_id, msg_payload)

    except WebSocketDisconnect:
        # حذف ws از clients
        if chat_id in clients and user_id in clients[chat_id]:
            clients[chat_id][user_id] = [w for w in clients[chat_id][user_id] if w != ws]
            if not clients[chat_id][user_id]:
                del clients[chat_id][user_id]

        # حذف از online_users
        if user_id in online_users:
            del online_users[user_id]

        await broadcast_online_users()