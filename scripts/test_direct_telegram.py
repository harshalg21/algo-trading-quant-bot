import requests
import sys
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

print("="*60)
print(" TESTING DIRECT TELEGRAM DISPATCH")
print("="*60)
print(f"Token: {TELEGRAM_BOT_TOKEN[:15]}...")
print(f"Chat ID: {TELEGRAM_CHAT_ID}")
print("="*60)

url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
msg = "🚨 **TEST ALERT FROM ALGO BOT**: Checking direct Telegram delivery right now!"
payload = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": msg,
    "parse_mode": "Markdown"
}

try:
    res = requests.post(url, json=payload, timeout=10)
    print(f"Telegram API Response Code: {res.status_code}")
    print(f"Telegram API Body: {res.text}")
except Exception as e:
    print(f"Error sending direct Telegram message: {e}")
