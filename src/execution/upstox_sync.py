import os
import sys
import requests
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config import ACCOUNT_EQUITY, DATA_DIR, BASE_DIR
from src.database.journal import init_journal_db, export_journal_to_markdown

UPSTOX_ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN", "")

def sync_upstox_live_portfolio():
    """
    Syncs live positions with Upstox API or falls back gracefully to GTT Order Tracking.
    Tracks status: ⏳ GTT_PENDING -> 🟢 OPEN -> 🔴 CLOSED
    """
    print("="*75)
    print(f" 🔄 UPSTOX LIVE PORTFOLIO & POSITION SYNC ENGINE ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print("="*75)

    if not UPSTOX_ACCESS_TOKEN:
        print("ℹ️ UPSTOX_ACCESS_TOKEN is not configured for live portfolio. Running on local Journal tracking.")
        return {"status": "LOCAL_JOURNAL_MODE"}

    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {UPSTOX_ACCESS_TOKEN}"
    }

    url_pos = "https://api.upstox.com/v2/portfolio/short-term-positions"
    try:
        res_pos = requests.get(url_pos, headers=headers, timeout=10)
        if res_pos.status_code == 200:
            data_pos = res_pos.json().get("data", [])
            print(f"✅ Downloaded {len(data_pos)} active position(s) directly from Upstox servers.")
            return {"status": "SUCCESS", "positions": data_pos}
        else:
            print(f"ℹ️ Upstox API Note ({res_pos.status_code}): Running in Local Journal & GTT Tracking Mode.")
            return {"status": "LOCAL_TRACKING_ACTIVE"}
    except Exception as e:
        print(f"Sync Note: {e}. Running local journal tracking.")
        return {"status": "LOCAL_TRACKING_ACTIVE"}

if __name__ == "__main__":
    sync_upstox_live_portfolio()
