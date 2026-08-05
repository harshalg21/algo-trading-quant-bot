import sys
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.alerts.telegram_bot import send_telegram_signal

def test_telegram_connection():
    print("="*60)
    print(" TESTING TELEGRAM BOT NOTIFICATION CONNECTION")
    print("="*60)
    print(f"BOT TOKEN : {'CONFIGURED ✅' if TELEGRAM_BOT_TOKEN else 'MISSING ❌'}")
    print(f"CHAT ID   : {'CONFIGURED ✅' if TELEGRAM_CHAT_ID else 'MISSING ❌'}")
    print("="*60)

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("\n❌ Telegram credentials missing in .env file.")
        print("Please update TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env first.")
        return

    print("\nSending test trade card to your Telegram phone app...")
    success = send_telegram_signal(
        symbol="SBIN.NS",
        signal_type="TEST BUY SIGNAL",
        entry_price=1027.40,
        stop_loss=1000.61,
        target_price=1094.36,
        quantity=37,
        risk_amount=991.07
    )

    if success:
        print("\n🎉 SUCCESS! Test message sent to your Telegram phone app!")
    else:
        print("\n❌ Failed to send Telegram message. Check token or internet connection.")

if __name__ == "__main__":
    test_telegram_connection()
