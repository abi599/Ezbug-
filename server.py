import sqlite3
import hashlib
from flask import Flask, request, jsonify, send_from_directory
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
DB = os.path.join(os.path.dirname(__file__), 'database.db')

def get_db():
    return sqlite3.connect(DB)

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user',
        expired TEXT
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS pending_orders (
        buyer_id INTEGER,
        msg_id INTEGER,
        username TEXT,
        password TEXT,
        expired TEXT,
        invoice TEXT
    )''')
    # Buat akun owner default
    try:
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ('owner', '43a0d17178a9d26c9e0fe9a74b0b45e38d32f27aed887a008a54bf6e033bf7b9', 'owner'))
    except:
        pass
    conn.commit()
    conn.close()

init_db()

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

@app.route('/')
def index():
    return send_from_directory('web', 'index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT username, role FROM users WHERE username=? AND password=?",
        (username, hash_password(password)))
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify({'status': 'success', 'username': user[0], 'role': user[1]})
    return jsonify({'status': 'error', 'message': 'Username atau password salah!'})

@app.route('/statistik')
def statistik():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE expired IS NULL")
    aktif = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM users WHERE expired IS NOT NULL AND expired < datetime('now')")
    expired = cursor.fetchone()[0]
    conn.close()
    return jsonify({'total_user': total, 'user_aktif': aktif, 'user_expired': expired, 'pendapatan': 0})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)
