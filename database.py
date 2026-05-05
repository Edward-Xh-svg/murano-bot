# database.py
import sqlite3

def init_db():
    conn = sqlite3.connect('murano.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            capital TEXT,
            founder_entity TEXT,
            secret_id TEXT,
            status TEXT,
            founder_name TEXT,
            shares TEXT,
            service TEXT,
            employees TEXT,
            shareholders TEXT,
            currency TEXT
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

init_db()
