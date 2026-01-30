import sqlite3

conn = sqlite3.connect("chat.db")
cursor = conn.cursor()

# نمایش همه جدول‌ها
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables:", tables)

# نمایش ستون‌های جدول messages
cursor.execute("PRAGMA table_info(messages);")
columns = cursor.fetchall()
print("Columns in messages:", columns)

# نمایش چند پیام نمونه
cursor.execute("SELECT * FROM messages LIMIT 10;")
rows = cursor.fetchall()
for row in rows:
    print(row)

conn.close()