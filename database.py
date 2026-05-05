# database.py
import sqlite3

def init_db():
    conn = sqlite3.connect('murano.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            data TEXT,
            secret_id TEXT,
            user_id INTEGER,
            status TEXT DEFAULT 'pending'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS secrets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            secret_code TEXT
        )
    ''')
    conn.commit()
    conn.close()

# تشغيل التهيئة عند الاستدعاء
init_db()
