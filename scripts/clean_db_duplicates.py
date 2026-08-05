import sqlite3
import sys
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DATA_DIR

def clean_duplicates():
    conn = sqlite3.connect(DATA_DIR / "trading_journal.db")
    cursor = conn.cursor()
    # Keep only the latest EXECUTED GOLDPETAL entry
    cursor.execute("DELETE FROM journal_entries WHERE symbol = 'GOLDPETAL' AND id NOT IN (SELECT max(id) FROM journal_entries WHERE symbol = 'GOLDPETAL');")
    conn.commit()
    conn.close()

    conn2 = sqlite3.connect(DATA_DIR / "trades.db")
    cursor2 = conn2.cursor()
    cursor2.execute("DELETE FROM positions WHERE symbol = 'GOLDPETAL' AND id NOT IN (SELECT max(id) FROM positions WHERE symbol = 'GOLDPETAL');")
    conn2.commit()
    conn2.close()

    print("🎉 Cleaned duplicate position entries! Active open positions = 1 (GOLDPETAL 3 Lots).")

if __name__ == "__main__":
    clean_duplicates()
