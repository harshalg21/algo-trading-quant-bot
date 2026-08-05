import sqlite3
from datetime import datetime
from pathlib import Path
from src.config import BASE_DIR

DB_PATH = BASE_DIR / "data" / "trades.db"

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            entry_date TEXT NOT NULL,
            entry_price REAL NOT NULL,
            stop_loss REAL NOT NULL,
            target_price REAL NOT NULL,
            quantity INTEGER NOT NULL,
            max_risk_inr REAL NOT NULL,
            holding_days INTEGER DEFAULT 0,
            status TEXT DEFAULT 'OPEN',
            exit_date TEXT,
            exit_price REAL,
            exit_reason TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_position(symbol: str, entry_price: float, stop_loss: float, target_price: float, quantity: int, max_risk_inr: float):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    entry_date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        INSERT INTO positions (symbol, entry_date, entry_price, stop_loss, target_price, quantity, max_risk_inr, holding_days, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0, 'OPEN')
    """, (symbol, entry_date, entry_price, stop_loss, target_price, quantity, max_risk_inr))
    conn.commit()
    conn.close()

def get_open_positions() -> list:
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, symbol, entry_date, entry_price, stop_loss, target_price, quantity, holding_days FROM positions WHERE status = 'OPEN'")
    rows = cursor.fetchall()
    conn.close()
    
    positions = []
    for r in rows:
        positions.append({
            "id": r[0],
            "symbol": r[1],
            "entry_date": r[2],
            "entry_price": r[3],
            "stop_loss": r[4],
            "target_price": r[5],
            "quantity": r[6],
            "holding_days": r[7]
        })
    return positions

def close_position(pos_id: int, exit_price: float, exit_reason: str):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    exit_date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        UPDATE positions 
        SET status = 'CLOSED', exit_date = ?, exit_price = ?, exit_reason = ?
        WHERE id = ?
    """, (exit_date, exit_price, exit_reason, pos_id))
    conn.commit()
    conn.close()

def increment_holding_days(pos_id: int, current_days: int):
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE positions SET holding_days = ? WHERE id = ?", (current_days + 1, pos_id))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
