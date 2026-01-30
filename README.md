# Mapsim Chat

A simple real-time chat application with end-to-end encryption (E2EE) for text and file messages.  
Users can register, login, and chat globally or privately. No admin panel is included.

---

## 🚀 Demo

🔗 **[Watch Demo](./#)**

---

## 💡 Features

- Global Chat Room
- Private Chat Between Users
- End-to-end Encryption For Messages
- File Sharing (images, video, PDF, other)
- JWT-based Authentication
- Persistent Chat History In SQLite
- Cross-platform: `Linux`, `macOS`, `Windows`

---

## 🛠️ Tech Stack

- Python 3.8+
- FastAPI (backend)
- SQLite (database)
- HTML / CSS / JavaScript (frontend)
- Optional: Uvicorn (ASGI server)
- JavaScript libs: libsodium for E2EE

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

---

### Step 3: Install dependencies

```bash
pip install --upgrade pip
```

```bash
pip install -r requirements.txt
```

---

### Step 4: Verify required folders and files

Ensure these folders exist:
- `uploads/`
- `app/static/`

> If `uploads/` doesn't exist, create it: 

```bash
mkdir uploads
```

---

### Step 5: Run the server

Navigate to the folder containing `main.py`:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- Open browser: `http://127.0.0.1:8000`  
- For remote VPS: replace `127.0.0.1` with your VPS IP

---

## ⚙️ Run as Systemd Service (Optional)


```bash
chmod +x setup_service.sh
sudo ./setup_service.sh
```
And 

```bash
chmod +x auto_clear_uploads.sh
sudo ./auto_clear_uploads.sh
```
Managment Command :

### * Status Service

```bash
systemctl status Mapsim_chat
```
```bash
systemctl status Mapsim_chat_auto_clear_uploads
```
### * Restart Service

```bash
systemctl restart Mapsim_chat
```
```bash
systemctl restart Mapsim_chat_auto_clear_uploads
```
### * Stop Service

```bash
systemctl stop Mapsim_chat
```
```bash
systemctl stop Mapsim_chat_auto_clear_uploads
```
### * Log View Service

```bash
journalctl -u Mapsim_chat -f
```
---

## ▶️ Access UI & APIs

- Global Chat UI: `http://<VPS-IP>:8000/static/index.html`

### Show Data In DB

1. Stop the server (CTRL+C) and run:

**Show Data From DB :**

2. Run `s_db.py` For Show Your Data In The DB

```bash
python s_db.py

```
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

---

## 🗂️ Database

SQLite database `chat.db` is automatically created on first run.
- Tables:
  - `users` → registered users
  - `chats` → chat rooms
  - `chat_members` → members of private chats
  - `messages` → all messages


---

## 🌐 Frontend
* Login and registration forms
* Chat UI with message bubbles
* File uploads (images, videos, PDFs)
* Online users list
* Private chat support (Coming Soon)
* E2EE encryption for all text messages

---

## 🔐 Security
- JWT authentication
- End-to-end encryption with libsodium
- Files stored in uploads/
- User `passwords` hashed with `pbkdf2_sha256` (macOS) or bcrypt (other OS)

---

## 📡 Notes for VPS Deployment
1. Make sure Python 3.8+ is installed.
2. Make uploads/ folder writable by the server user.
3. Use Uvicorn or Gunicorn with ASGI for production.
4. Optional: run as systemd service:

* Example:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 📝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

---

## 📜 License

This project is licensed under the MIT License. See [LICENSE](./LICENSE.txt) for details.

