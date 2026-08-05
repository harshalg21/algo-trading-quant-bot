import sqlite3
import sys
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DATA_DIR
from src.database.journal import init_journal_db, export_journal_to_markdown

init_journal_db()
conn = sqlite3.connect(DATA_DIR / "trading_journal.db")
cursor = conn.cursor()

# Reset DB entry #1 to GTT SCHEDULED (0/3) with 3 Lots and ₹0 Margin Blocked
cursor.execute("""
    UPDATE journal_entries
    SET status = 'SCHEDULED', quantity = 3, margin_used = 0.0, upstox_charges = 78.20, notes = 'GTT Order Scheduled on Upstox (0/3 Lots)'
    WHERE symbol = 'GOLDPETAL';
""")
conn.commit()
conn.close()

export_journal_to_markdown()
print("🎉 TRADING_JOURNAL.md successfully updated to GTT SCHEDULED (0/3) with 3 Lots & ₹78.20 Upstox Charges!")
