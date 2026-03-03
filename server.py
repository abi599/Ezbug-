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
        cursor.execute('''CREATE TABLE IF NOT EXISTS sessions (
        username TEXT PRIMARY KEY,
        device_id TEXT,
        last_login TEXT
    )''')
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
        device_id = data.get('device_id', 'unknown')
        conn2 = get_db()
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT device_id FROM sessions WHERE username=?", (user[0],))
        existing = cursor2.fetchone()
        if existing and existing[0] != device_id and user[1] != 'owner':
            conn2.close()
            return jsonify({'status': 'error', 'message': 'Akun ini sudah dipakai di perangkat lain!'})
        cursor2.execute("INSERT OR REPLACE INTO sessions VALUES (?, ?, datetime('now'))", (user[0], device_id))
        conn2.commit()
        conn2.close()
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

import os
import subprocess

EZBUG_DIR = os.path.dirname(__file__)
ALLOWED_FILES = ['bot1.py', 'bot2.py', 'server.py', 'web/index.html']

@app.route('/panel/log')
def panel_log():
    try:
        log = open(os.path.join(EZBUG_DIR, 'bot1.log')).read()[-3000:]
    except:
        log = "Log tidak tersedia"
    return jsonify({'log': log})

@app.route('/panel/files')
def panel_files():
    return jsonify({'files': ALLOWED_FILES})

@app.route('/panel/file', methods=['GET'])
def panel_get_file():
    name = request.args.get('name')
    if name not in ALLOWED_FILES:
        return jsonify({'error': 'File tidak diizinkan'})
    try:
        content = open(os.path.join(EZBUG_DIR, name)).read()
        return jsonify({'content': content})
    except:
        return jsonify({'content': ''})

@app.route('/panel/file', methods=['POST'])
def panel_save_file():
    data = request.json
    name = data.get('name')
    content = data.get('content')
    if name not in ALLOWED_FILES:
        return jsonify({'message': 'File tidak diizinkan!'})
    try:
        open(os.path.join(EZBUG_DIR, name), 'w').write(content)
        return jsonify({'message': f'File {name} berhasil disimpan!'})
    except Exception as e:
        return jsonify({'message': f'Gagal: {str(e)}'})

@app.route('/panel/start', methods=['POST'])
def panel_start():
    return jsonify({'message': 'Bot sudah jalan di Railway!'})

@app.route('/panel/restart', methods=['POST'])
def panel_restart():
    return jsonify({'message': 'Restart tidak tersedia di Railway. Push ke GitHub untuk update!'})

@app.route('/panel/stop', methods=['POST'])
def panel_stop():
    return jsonify({'message': 'Stop tidak tersedia di Railway!'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False)


