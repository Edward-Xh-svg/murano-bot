import sqlite3
import json
from datetime import datetime


class Database:
    def __init__(self, db_path="hostaka.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    capital TEXT,
                    founding_entity TEXT,
                    stock_status TEXT,
                    founder_name TEXT,
                    shares TEXT,
                    service TEXT,
                    employees TEXT,
                    shareholders TEXT,
                    currency TEXT,
                    analysis TEXT,
                    user_id INTEGER,
                    created_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS secret_ids (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_name TEXT NOT NULL,
                    secret_id TEXT NOT NULL UNIQUE,
                    used INTEGER DEFAULT 0
                )
            """)
            conn.commit()

    def verify_secret_id(self, secret_id: str, entity_name: str) -> bool:
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT id FROM secret_ids WHERE secret_id=? AND entity_name=? AND used=0",
                (secret_id, entity_name)
            ).fetchone()
            return row is not None

    def add_secret_id(self, entity_name: str, secret_id: str):
        """يُستخدم من قِبل الأدمن لإضافة معرفات سرية"""
        with self._get_conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO secret_ids (entity_name, secret_id) VALUES (?, ?)",
                (entity_name, secret_id)
            )
            conn.commit()

    def register_company(self, data: dict, analysis: str, user_id: int):
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO companies
                (name, capital, founding_entity, stock_status, founder_name,
                 shares, service, employees, shareholders, currency, analysis, user_id, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, (
                data['company_name'], data['capital'], data['founding_entity'],
                data['stock_status'], data['founder_name'], data['shares'],
                data['service'], data['employees'], data['shareholders'],
                data['currency'], analysis, user_id,
                datetime.now().isoformat()
            ))
            conn.commit()

    def get_all_companies(self):
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT name, stock_status, currency, user_id FROM companies ORDER BY created_at DESC"
            ).fetchall()
            return [{'name': r[0], 'status': r[1], 'currency': r[2], 'user_id': r[3]} for r in rows]

    def get_all_registered_companies_full(self):
        with self._get_conn() as conn:
            rows = conn.execute("SELECT * FROM companies").fetchall()
            columns = ['id', 'name', 'capital', 'founding_entity', 'stock_status',
                       'founder_name', 'shares', 'service', 'employees', 'shareholders',
                       'currency', 'analysis', 'user_id', 'created_at']
            return [dict(zip(columns, r)) for r in rows]
