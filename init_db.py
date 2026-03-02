import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

conn = sqlite3.connect('/data/data/com.termux/files/home/ezbug/database.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        expired TEXT DEFAULT NULL
    )
''')

cursor.execute('''
    INSERT OR IGNORE INTO users (username, password, role)
    VALUES (?, ?, ?)
''', ('owner', hash_password('owner123'), 'owner'))

conn.commit()
conn.close()
print("Database berhasil dibuat!")
