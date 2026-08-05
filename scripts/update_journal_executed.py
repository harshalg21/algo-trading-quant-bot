import sqlite3
import sys
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DATA_DIR
from src.database.db import add_position
from src.database.journal import init_journal_db, export_journal_to_markdown

init_journal_db()
conn = sqlite3.connect(DATA_DIR / "trading_journal.db")
cursor = conn.cursor()

# Update GOLDPETAL entry to EXECUTED (3/3) with 3 Lots & ₹3,984.75 Margin Blocked
cursor.execute("""
    UPDATE journal_entries
    SET status = 'EXECUTED', quantity = 3, margin_used = 3984.75, upstox_charges = 78.20, notes = 'GTT Order Triggered & Holding on Upstox (3/3 Lots)'
    WHERE symbol = 'GOLDPETAL';
""")
conn.commit()
conn.close()

# Also register active open position in trades.db
add_position("GOLDPETAL", 14340.0, 14023.0, 15150.0, 3, 3984.75)

export_journal_to_markdown()
print("🎉 TRADING_JOURNAL.md successfully updated to 🟢 EXECUTED (3/3) with 3 Lots & ₹3,984.75 Margin Blocked!")
