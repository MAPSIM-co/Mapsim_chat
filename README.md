# Madol Chat

An educational multiplication table game for practice, training, and competition.

## Language 

**- [زبان فارسی](./README_FA.md)**

---

## 🚀 Demo



🔗 **[Watch Demo Game](./#)**

---

## 💡 Features

- Practice multiplication tables from 1 to 12
- Timed quizzes and scoring
- Track player progress and high scores
- Cross-platform: Linux, Windows, macOS
- Admin panel for managing players and admins
- Practice mode with review of wrong answers
- Statistics APIs for players and questions

---

## 🛠️ Tech Stack

- Python 3.8+
- FastAPI (backend)
- SQLite (database)
- HTML / CSS / JavaScript (frontend)
- Optional: Uvicorn (ASGI server)

---

## 📦 Installation & Setup

### Step 0: Update & Upgrade Your OS (Linux)

```bash
sudo apt update
sudo apt upgrade -y
```

### Step 1: Clone the repository

```bash
git clone https://github.com/MAPSIM-co/zarb-table-game.git
cd zarb-table-game
```
- OR
  
If You Can Update Your Existing Repository :

```bash
cd ~/zarb-table-game
git pull
```

Install Python Virtual Environment

```bash
sudo apt update
sudo apt install -y python3-venv

```
- OR (if you want Python 3.10 specifically)

```bash
sudo apt install -y python3.10-venv
```

### Step 2: Create and activate a virtual environment

#### Linux / macOS

```bash
python3 -m venv venv
source venv/bin/activate
```
#### Windows (PowerShell)

```bash
python -m venv venv
.\venv\Scripts\activate
```
⚠️ Make sure your virtual environment is activated. Your terminal should show (venv) at the beginning of the prompt.


### Step 3: Install dependencies

- Install  `requirements.txt` In Your OS :

```bash
pip install -r requirements.txt
```

### Step 4: Verify required folders and files

Make sure the following folders exist:


- static/
- admin/
- Dashboard/
- practice/
- report-ui/


* Also ensure static/rewards.json exists. If not, create an empty JSON array:

```bash
[]

```
OR

```bash
[
    {
        "name": "Reward Name1",
        "desc": "Description Reward1"
    },
    {
        "name": "Reward Name2",
        "desc": "Description Reward2"
    }
]
```

### Step 5: Run the server

Navigate to the folder where ""main.py"" is located and run:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

* Open browser: http://127.0.0.1:8000
* For remote VPS, replace 127.0.0.1 with your VPS IP Or Your Computer Network

---

## ⚙️ Make Service File
```bash
chmod +x setup_service.sh
sudo ./setup_service.sh
```
Managment Command :

### Status Service

```bash
systemctl status zarb-table-game
```
### Restart Service

```bash
systemctl restart zarb-table-game
```
### Stop Service

```bash
systemctl stop zarb-table-game
```
### Log View Service

```bash
journalctl -u zarb-table-game -f
```
---
## ▶️ Access UI & APIs

* Admin UI: http://127.0.0.1:8000/admin/panel.html

### Make Admin

* First CTRL+C (For Stop Server)

RUN:
```bash
python add_admin.py
```

Now :

* Your username = `admin`
* Your password = `admin` 

👑 You Can Make `New User` And Visit `Report` User



Dashboard: http://127.0.0.1:8000/dashboard/index.html

---

## 📡 API Reference – Zarb Table Game

### 1️⃣ Multiplayer Game APIs

| Endpoint | Method | Description | Request Parameters | Response Example |
|----------|--------|-------------|------------------|-----------------|
| `/start` | POST | Start a multiplayer game | `{"players":["alice","bob"], "families":[2,3,4], "questions":10, "time":20}` | `{"status":"started"}` |
| `/question` | GET | Get the current question | None | `{"end": false, "question":"2x3", "player":"alice", "number":1, "total":10, "scores":{"alice":0,"bob":0}, "time":20}` |
| `/answer` | POST | Submit an answer | `{"player":"alice", "question":"2x3", "answer":6}` | `{"correct": true, "scores":{"alice":1,"bob":0}}` |
| `/finish` | POST | Finish the game and save results | `{"players":["alice","bob"], "scores":{"alice":5,"bob":4}}` | `{"status":"ok"}` |

---

### 2️⃣ Practice Mode APIs

| Endpoint | Method | Description | Request Parameters | Response Example |
|----------|--------|-------------|------------------|-----------------|
| `/practice/start` | POST | Start a practice session | `{"player":"john", "families":[2,3,4], "questions":10, "time":20}` | `{"status":"practice_started", "questions":[{"a":2,"b":3,"answer":6}, ...]}` |
| `/practice/answer` | POST | Submit answer in practice mode | `{"player":"john", "question":"2x3", "answer":6}` | `{"correct": true, "correct_answer":6, "scores":{"john":1}}` |
| `/api/practice-players` | GET | List all players who practiced | None | `["john","alice"]` |
| `/api/practice/stats/{player}` | GET | Practice stats (correct/wrong) | `player` (str) | `{"correct":5,"wrong":3}` |
| `/api/practice/wrong/{player}` | GET | List wrong answers of a player | `player` (str) | `[{"question":"3x7","answer":20}]` |
| `/api/practice/questions-wrong` | GET | Questions with highest wrong count | None | `[{"question":"3x7","wrong_count":4}]` |

---

### 3️⃣ Admin & Reports APIs

| Endpoint | Method | Description | Request Parameters | Response Example |
|----------|--------|-------------|------------------|-----------------|
| `/admin/login` | POST | Admin login | `username`, `password` (form-data) | `{"success": true, "admin_id": 1, "is_superadmin": 1}` |
| `/admin/add-player` | POST | Add a new player | `name` (form-data) | `{"success": true, "msg": "بازیکن ثبت شد!"}` |
| `/admin/add-admin` | POST | Add new admin (requires superadmin) | `username`, `password`, `is_superadmin` (0/1), `current_admin_id` | `{"success": true, "msg": "ادمین جدید ثبت شد!"}` |
| `/api/players` | GET | List all registered players | None | `["alice","bob"]` |
| `/api/wrong/{player}` | GET | Wrong answers of a player | `player` (str) | `[{"question":"2x3","answer":5}]` |
| `/api/stats/{player}` | GET | Correct & wrong count | `player` (str) | `{"correct":5,"wrong":3}` |
| `/api/questions-wrong` | GET | Questions with highest wrong count | None | `[{"question":"3x7","wrong_count":4}]` |
| `/api/wrong-stats/{player}` | GET | Number of wrong answers per question for a player | `player` (str) | `[{"question":"3x7","wrong_count":2}]` |
| `/api/right-stats/{player}` | GET | Number of correct answers per question for a player | `player` (str) | `[{"question":"2x3","right_count":3}]` |


## Example: Start a Practice Session

Curl Examples:

### Start game

```bash
curl -X POST "http://127.0.0.1:8000/start" \
-H "Content-Type: application/json" \
-d '{"players":["alice","bob"],"families":[2,3,4],"questions":10,"time":20}'
```

### Get question

```bash
curl "http://127.0.0.1:8000/question"
```

### Submit answer

```bash
curl -X POST "http://127.0.0.1:8000/answer" \
-H "Content-Type: application/json" \
-d '{"player":"alice","question":"2x3","answer":6}'
```
### Finish game

```bash
curl -X POST "http://127.0.0.1:8000/finish" \
-H "Content-Type: application/json" \
-d '{"players":["alice","bob"],"scores":{"alice":5,"bob":4}}'
```
### Start a Multiplayer Game

```bash
curl -X POST "http://127.0.0.1:8000/practice/start" \
-H "Content-Type: application/json" \
-d '{"player":"john","families":[2,3,4],"questions":10,"time":20}'
```

## 🗂️ Database

SQLite database game.db is automatically created on first run.
  - Tables:
    * players → registered players
    * admins → admin users
    * results → game scores
    * answers → all submitted answers
    * practice_answers → answers from practice mode

## 🔐 Admin Management

  * Login
    * POST /admin/login
    * Form Data:
      - username
      - password
  * Add Admin (requires superadmin)
    * POST /admin/add-admin
    * Form Data:
      - username
      - password
      - is_superadmin (0 or 1)
      - current_admin_id (your admin id)
  * Add Player
    * POST /admin/add-player
    * Form Data:
      - name

## 📊 Reports & Stats

- `/api/players → List all players`
- `/api/wrong/{player} → Wrong answers of a player`
- `/api/stats/{player} → Correct & wrong count`
- `/api/questions-wrong → Questions with highest wrong count`
- `/api/practice-players → Practice mode players`
- `/api/practice/stats/{player} → Practice stats`

## 📝 Contributing
Contributions are welcome! Feel free to open issues or submit pull requests.

## 📜 License
This project is licensed under the MIT License. See the [LICENSE](./LICENSE.txt) file for details.
