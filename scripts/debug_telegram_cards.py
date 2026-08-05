import requests
import json
import sys
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

def debug_send():
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    eq_text = (
        "====================================\n"
        "📈 *1. NSE EQUITY SWING TRADE CARDS*\n"
        "====================================\n\n"
        "📌 *SUNPHARMA.NS*  | Win Score: *89.8/100*\n"
        "   • 🟢 15M + 1H + 1D PERFECTLY ALIGNED\n"
        "   • *BUY*: ₹1,940.50 | *SL*: ₹1,908.20\n"
        "   • 🎯 *TARGET 1 (Scale 50% & SL to Cost)*: ₹1,988.95 (+1.5R)\n"
        "   • 🎯 *TARGET 2 (Final Target)*: ₹2,052.75 (+2.5R)\n"
        "   • *REC. QTY*: 4 Shares (Max Risk: ₹165.20)\n\n"
        "📌 *DLF.NS*  | Win Score: *78.2/100*\n"
        "   • 🟢 15M + 1H + 1D PERFECTLY ALIGNED\n"
        "   • *BUY*: ₹662.00 | *SL*: ₹638.10\n"
        "   • 🎯 *TARGET 1 (Scale 50% & SL to Cost)*: ₹697.85 (+1.5R)\n"
        "   • 🎯 *TARGET 2 (Final Target)*: ₹728.40 (+2.5R)\n"
        "   • *REC. QTY*: 7 Shares (Max Risk: ₹180.60)\n\n"
        "====================================\n"
        "🥇 *2. MCX COMMODITY FUTURES CARDS*\n"
        "====================================\n\n"
        "🥇 *GOLDPETAL 31AUG26 FUT*  | Win Score: *85.0/100*\n"
        "   • 🟢 15M + 1H + 1D PERFECTLY ALIGNED\n"
        "   • *BUY FUTURES*: ₹14,360.00 | *SL*: ₹14,190.00\n"
        "   • 🎯 *TARGET 1 (Book 50% & SL to Breakeven)*: ₹14,615.00 (+1.5R)\n"
        "   • 🎯 *TARGET 2 (Final Target)*: ₹14,785.00 (+2.5R)\n"
        "   • *MARGIN REQ*: ₹1,328.25 per lot"
    )

    inline_buttons = [
        [
            {"text": "⏳ SUNPHARMA SCHEDULED", "callback_data": "confirm_sched_EQ_SUNPHARMA.NS_1940.5_1908.2_2052.75_4"},
            {"text": "🟢 SUNPHARMA EXECUTED", "callback_data": "confirm_exec_EQ_SUNPHARMA.NS_1940.5_1908.2_2052.75_4"}
        ],
        [
            {"text": "⏳ DLF SCHEDULED", "callback_data": "confirm_sched_EQ_DLF.NS_662.0_638.1_728.4_7"},
            {"text": "🟢 DLF EXECUTED", "callback_data": "confirm_exec_EQ_DLF.NS_662.0_638.1_728.4_7"}
        ],
        [
            {"text": "⏳ GOLDPETAL SCHEDULED (3 Lots)", "callback_data": "confirm_sched_CMD_GOLDPETAL_14360.0_14190.0_14785.0_3_3984.75"},
            {"text": "🟢 GOLDPETAL EXECUTED (3 Lots)", "callback_data": "confirm_exec_CMD_GOLDPETAL_14360.0_14190.0_14785.0_3_3984.75"}
        ]
    ]

    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": eq_text,
        "parse_mode": "Markdown",
        "reply_markup": {"inline_keyboard": inline_buttons}
    }

    res = requests.post(url, json=payload, timeout=10)
    print(f"Status Code: {res.status_code}")
    print(f"Response: {res.text}")

if __name__ == "__main__":
    debug_send()
