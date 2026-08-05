import os
import sys

# Fix OpenBLAS Threading at top
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import time
import requests
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.database.db import add_position
from src.database.journal import log_trade_to_journal

def answer_callback(callback_id: str, text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
    try:
        requests.post(url, json={"callback_query_id": callback_id, "text": text, "show_alert": True}, timeout=5)
    except Exception as e:
        print(f"Error answering callback: {e}")

def send_chat_message(text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=5)
    except Exception as e:
        print(f"Error sending message: {e}")

def poll_telegram_updates():
    if not TELEGRAM_BOT_TOKEN:
        print("[LISTENER]: Telegram bot token missing.")
        return

    print("="*60)
    print(" 🤖 TELEGRAM GTT ORDER & JOURNAL LISTENER RUNNING")
    print(" Listening for GTT SCHEDULED (0/3) & EXECUTED (3/3) trade taps...")
    print("="*60)

    offset = None
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
            params = {"timeout": 10}
            if offset:
                params["offset"] = offset

            res = requests.get(url, params=params, timeout=15)
            data = res.json()

            if data.get("ok") and data.get("result"):
                for update in data["result"]:
                    offset = update["update_id"] + 1

                    if "callback_query" in update:
                        cb = update["callback_query"]
                        cb_id = cb["id"]
                        cb_data = cb.get("data", "")

                        if cb_data.startswith("confirm_sched_") or cb_data.startswith("confirm_exec_"):
                            is_sched = cb_data.startswith("confirm_sched_")
                            parts = cb_data.split("_")[2:]
                            
                            if len(parts) >= 6:
                                trade_type = parts[0]
                                symbol = parts[1]
                                price = float(parts[2])
                                sl = float(parts[3])
                                tp = float(parts[4])
                                qty = int(parts[5])
                                margin = float(parts[6]) if len(parts) > 6 else 0.0

                                status_str = "SCHEDULED" if is_sched else "EXECUTED"
                                margin_blocked = 0.0 if is_sched else margin
                                note_str = f"GTT Order Scheduled on Upstox (0/{qty} Lots)" if is_sched else f"GTT Order Triggered & Holding on Upstox ({qty}/{qty} Lots)"

                                # Log into journal DB & update TRADING_JOURNAL.md
                                log_trade_to_journal(
                                    trade_type=trade_type,
                                    symbol=symbol,
                                    entry_price=price,
                                    stop_loss=sl,
                                    target_price=tp,
                                    quantity=qty,
                                    margin_used=margin_blocked,
                                    status=status_str,
                                    notes=note_str
                                )

                                if not is_sched:
                                    add_position(symbol, price, sl, tp, qty, margin_blocked)

                                alert_msg = f"⏳ GTT Order Scheduled for {symbol} ({qty} Lots)!" if is_sched else f"🟢 Trade Executed for {symbol} ({qty} Lots)!"
                                answer_callback(cb_id, alert_msg)
                                
                                send_chat_message(
                                    f"📖 **JOURNAL UPDATED**: Logged **{symbol}** as **{status_str}** "
                                    f"({qty} Lots @ ₹{price:,.2f} | Margin Blocked: ₹{margin_blocked:,.2f}) into `TRADING_JOURNAL.md`!"
                                )

                        elif cb_data.startswith("confirm_skipped_"):
                            symbol = cb_data.split("_")[-1]
                            answer_callback(cb_id, f"❌ {symbol} marked as skipped.")
                            send_chat_message(f"❌ **TRADE SKIPPED**: {symbol} setup skipped.")

        except Exception as e:
            print(f"[LISTENER ERROR]: {e}")
            time.sleep(5)

if __name__ == "__main__":
    poll_telegram_updates()
