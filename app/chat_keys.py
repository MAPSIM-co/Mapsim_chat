# app/chat_keys.py
import os
import base64

GLOBAL_CHAT_KEY = base64.b64encode(os.urandom(32)).decode()