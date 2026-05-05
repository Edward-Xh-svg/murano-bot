# admin_add_secret.py
import sqlite3

def add_secret(secret_code):
    conn = sqlite3.connect('murano.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO secrets (secret_code) VALUES (?)", (secret_code,))
    conn.commit()
    conn.close()
    print(f"✅ تمت إضافة المعرف السري بنجاح: {secret_code}")

if __name__ == '__main__':
    code = input("أدخل المعرف السري الجديد: ")
    add_secret(code)
