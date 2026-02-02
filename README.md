# Mapsim Chat

A real-time chat application with strong security design, encrypted messaging, file sharing, and WebSocket-based communication.  
Designed for developers who want **full control**, **transparent architecture**, and **self-hosted security**.

---

## 🚀 Demo

**🔗 Demo can be deployed locally or on VPS after installation.**

---

## 💡 Features

- Global public chat room
- Private chat (architecture ready)
- Encrypted messages (runtime session key)
- Secure file upload & download
- JWT-based authentication
- Key versioning system (server restart = new session key)
- WebSocket real-time communication
- MySQL database support
- Linux / macOS / Windows

---

## 🛠️ Tech Stack

- Python 3.8+
- FastAPI (backend)
- SQLite (database)
- HTML / CSS / JavaScript (frontend)
- Optional: Uvicorn (ASGI server)
- JavaScript libs: libsodium for E2EE

---

## 🔐 Security Architecture (Important)

### 1. Authentication
- Users authenticate via **JWT**
- JWT contains:
  - user id (`sub`)
  - username
  - expiration (`exp`)
- Signed with `SECRET_KEY` from `.env`

### 2. Message Encryption Model
- On **every server restart**:
  - A new `GLOBAL_CHAT_KEY` is generated
  - Encrypted using `SECRET_KEY`
  - Stored in `key_versions` table
- Old keys are **never deleted automatically**
- This allows:
  - Message recovery
  - Key rotation
  - Forward secrecy per session

> ⚠️ This is **session-based encryption**, not Signal-style E2EE  
> Server **cannot read messages without keys**, but keys exist encrypted in DB.

---

### 3. Files
- Stored physically in `/uploads`
- Paths stored in DB
- Access controlled by WebSocket + JWT

---
## 🧠 Threat Model Summary

| Threat | Status |
|------|------|
| Fake JWT | ❌ Blocked |
| WebSocket hijack | ❌ Blocked |
| Token replay | ❌ Expired |
| DB leak | 🔒 Encrypted keys |
| Server admin | ⚠️ Trusted |
| MITM (no TLS) | ❌ Use HTTPS/WSS |

---

## 🗂 Project Structure

```
Mapsim_chat
├─ .env
├─ README.md
├─ LICENSE.txt
├─ requirements.txt
├─ app/
│  ├─ main.py
│  ├─ config.py
│  ├─ db.py
│  ├─ auth.py
│  ├─ websocket.py
│  ├─ chat_keys.py
│  └─ static/
│     ├─ index.html
│     ├─ chat.js
│     ├─ crypto-e2ee.js
│     ├─ sodium.min.js
│     └─ style.css
├─ uploads/
├─ auto_clear_uploads.py
├─ auto_clear_uploads.sh
├─ clear_data.py
└─ setup_service.sh
```
---

## 📦 Installation & Setup

### Step 0: Update & Upgrade Your OS (Linux)

```bash
sudo apt update
sudo apt upgrade -y
```

### Step 1: Clone the repository

```bash
git clone https://github.com/MAPSIM-co/Mapsim_chat.git
cd Mapsim_chat
```

- If you already have it locally, just pull

```bash
cd ~/Mapsim_chat
git pull
```

---

### Step 2: Create and activate a Python virtual environment

#### Install Python & Virtual Environment

* Install Python:

##### Linux / macOS

```bash
sudo apt install -y python3-venv python3-pip
```

##### Activation Environment

```bash
python3 -m venv venv
source venv/bin/activate

```

##### Windows (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\activate

```

> ⚠️ Make sure your virtual environment is activated. Your terminal should show `(venv)`.


### Step 3: Install dependencies

```bash
pip install --upgrade pip
```

```bash
pip install -r requirements.txt
```


### Step 4: Verify required folders and files

Ensure these folders exist:
- `uploads/`
- `app/static/`

> If `uploads/` doesn't exist, create it: 

```bash
mkdir uploads
```

---

## 🗄 Database Setup (MySQL – FULL)

MySQL database `chatdb` is automatically created on first run.
- Tables:
  - `users` → registered users
  - `chats` → chat rooms
  - `chat_members` → members of private chats
  - `messages` → all messages
  - `files` → Upload file
  - `key_versions` → Version key generate


### 1. Install MySQL
```bash
sudo apt install mysql-server -y
```

### 2. Login
```bash
mysql -u root -p
```

### 3. Create Database & User
```sql
CREATE DATABASE chatdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE USER 'chatuser'@'localhost' IDENTIFIED BY 'STRONG_PASSWORD';
GRANT ALL PRIVILEGES ON chatdb.* TO 'chatuser'@'localhost';
FLUSH PRIVILEGES;
```

### 4. Verify
```sql
USE chatdb;
SHOW TABLES;
```

> Tables are auto-created on first run

### Other Databse Command For Use  

  ```
  mysql -u root -p

  USE chatdb; 

  SHOW TABLES;

  SHOW CREATE TABLE <Table Name>;

  SELECT * FROM <Table Name>;

  TRUNCATE TABLE <Table Name>;
  -OR-
  DELETE FROM <Table Name>;

  DROP TABLE <Table Name>;

  DROP DATABASE chatdb;

  CREATE DATABASE chatdb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

  ```

---
## 🔑 Environment File (.env)

Create `.env` in project root:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=chatdb
DB_USER=chatuser
DB_PASS=STRONG_PASSWORD

SECRET_KEY=BASE64_32_BYTE_KEY

UPLOAD_DIR=uploads
UPLOAD_MAX_SIZE_GB=3
UPLOAD_CHECK_INTERVAL=14400
DEBUG=false
```

Generate key:
```bash
python - <<EOF
import base64, os
print(base64.b64encode(os.urandom(32)).decode())
EOF
```


## ▶️ Run Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open:
```
http://127.0.0.1:8000/static/index.html
```

- Open browser: `http://127.0.0.1:8000`  
- For remote VPS: replace `127.0.0.1` with your VPS IP

---

## ⚙️ Run as systemd Services (Optional)

This project can be deployed as **two systemd services** for production use:

1. **Main FastAPI Service** → `Mapsim_chat`
2. **Auto Clear Uploads Service** → `Mapsim_chat_auto_clear_uploads`

> ⚠️ **Important Notes**
>
> - Project path: `/root/Mapsim_chat`
> - Setup scripts **must be executed as root**
> - Do **NOT** manually activate virtualenv
> - Do **NOT** use `sudo` if you are already logged in as `root`

---

## 1️⃣ Enable Main Service (Mapsim_chat)

### If you are **root user**
```bash
cd /root/Mapsim_chat
chmod +x setup_service.sh
./setup_service.sh
```

### If you are **NOT root**
```bash
cd /root/Mapsim_chat
chmod +x setup_service.sh
sudo ./setup_service.sh
```

---

## 2️⃣ Enable Auto Clear Uploads Service (ACU)

This service automatically:
- Monitors the `uploads/` directory size
- Clears uploaded files when the size limit is exceeded
- Deletes all records from the `messages` table in SQLite

### If you are **root user**
```bash
cd /root/Mapsim_chat
chmod +x auto_clear_uploads.sh
./auto_clear_uploads.sh
```

### If you are **NOT root**
```bash
cd /root/Mapsim_chat
chmod +x auto_clear_uploads.sh
sudo ./auto_clear_uploads.sh
```

---

## 🛠 Service Management Commands

### 🔍 Check service status
```bash
systemctl status Mapsim_chat
```

```bash
systemctl status auto_clear_uploads
```

---

### 🔄 Restart services
```bash
systemctl restart Mapsim_chat
```

```bash
systemctl restart auto_clear_uploads
```

---

### ⛔ Stop services
```bash
systemctl stop Mapsim_chat
```

```bash
systemctl stop auto_clear_uploads
```
---

### 📜 View service logs (live)
```bash
journalctl -u Mapsim_chat -f
```
---

### ✅ Behavior Summary

- Both services start automatically after server reboot
- systemd manages process lifecycle and restarts
- Virtual environment is handled internally
- No manual background process management is required

---

## 🧹 Manual Maintenance

- Clean the `uploads/` directory size To ZIRO
- Deletes all records from the `messages` table 
- Deletes all records from the `files` table 
- Deletes all records from the `key_versions` table 


1. Run Command:
```bash
chmod +x clear_data.py
```
2. 
```bash
python3 clear_data.py
```
- OR
```bash
python clear_data.py
```

Your OutPut :
```
uploads cleared
messages cleared
files cleared
key_versions cleared
```
3. Check For `Uploads` Folder & DB Messages Table:

* First Check Uploads Folder :

```bash
ls -lh uploads
```
* And Then DB : 

```bash
mysql -u root -p
```
Entry your Password DB root User:

```bash
USE chatdb;
SHOW TABLES;
```
In The MySQL DB :

```bash
SELECT * FROM messages;
```
If your Out Put = **0** Is ****OK**** ✅

```bash
.exit
```

💡 You can use up command for another table ...
---

## Change Port Service

1. Edit `Mapsim_chat.service` File
```bash
nano /etc/systemd/system/Mapsim_chat.service
```
2. Find This Line :

**`ExecStart=/root/Mapsim_chat/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000`**

And Change To (YOUR-PORT):

**`ExecStart=/root/Mapsim_chat/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port`** ****<span style="color:red;">8001</span>****


3. Reload Services
   
```bash
systemctl daemon-reload
```

4. Restart Services
   
```bash
systemctl restart Mapsim_chat
```

5. Check Service Status
   
```bash
systemctl status Mapsim_chat
```

## ▶️ Access UI & APIs

- Global Chat UI: `http://<VPS-IP>:8000/static/index.html`


---

## ⚡ API Reference – Mapsim Chat

### 1️⃣ Authentication

| Endpoint | Method | Description | Request |
|----------|--------|-------------|---------|
| `/register/` | POST | Register a new user | `username`, `password`, `email` (optional) |
| `/login/` | POST | Login and get JWT token | `username`, `password` |

### 2️⃣ Messages

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/messages/?chat_id=global` | GET | Get messages for chat (`global` or private chat name) |
| `/upload/` | POST | Upload a file (returns `file_url`) |

### 3️⃣ WebSocket

| Endpoint | Description |
|----------|-------------|
| `/ws` | Connect WebSocket with JWT token and chat_name |

**Example WebSocket URL:**

```
ws://127.0.0.1:8000/ws?token=<JWT_TOKEN>&chat_name=global
```

**Message format (JSON):**

- Text message:

```json
{
  "type": "text",
  "text": "<encrypted_text>",
  "chat_name": "global"
}
```

- File message:

```json
{
  "type": "file",
  "text": "/uploads/<filename>",
  "chat_name": "global"
}
```

## 🧪 Security Test Example

Fake token test:
```js
new WebSocket("ws://localhost:8000/ws?token=FAKE&chat_name=global")
```
Expected:
❌ Connection rejected

---

## ⚖️ Comparison

| App | This Project |
|---|---|
| Mapsim Chat | Transparent / Self-hosted |


## 📝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

---

## 📜 License

This project is licensed under the MIT License. See [LICENSE](./LICENSE.txt) for details.
