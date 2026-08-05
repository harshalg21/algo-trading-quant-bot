import sqlite3
import sys
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.database.db import DB_PATH, init_db

def reset_database():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM positions;")
    conn.commit()
    conn.close()
    print("="*60)
    print(" 🧹 DATABASE RESET SUCCESSFULLY!")
    print(" All test positions cleared. Active Open Trades count: 0")
    print("="*60)

if __name__ == "__main__":
    reset_database()
