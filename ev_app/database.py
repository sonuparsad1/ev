import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "ev_data.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash BLOB NOT NULL,
                role TEXT NOT NULL,
                failed_attempts INTEGER DEFAULT 0,
                is_locked INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_name TEXT NOT NULL,
                vehicle_number TEXT UNIQUE NOT NULL,
                battery_capacity REAL NOT NULL,
                charging_type TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_number TEXT NOT NULL,
                energy REAL NOT NULL,
                cost REAL NOT NULL,
                duration REAL NOT NULL,
                charged_at TEXT DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def query(sql, params=(), one=False):
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        return rows[0] if (rows and one) else rows


def execute(sql, params=()):
    with get_conn() as conn:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
