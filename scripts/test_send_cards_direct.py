import sys
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.alerts.telegram_bot import send_combined_clean_trade_cards
from src.database.journal import send_eod_telegram_journal_summary

eq_test = [
    {"symbol": "SUNPHARMA.NS", "price": 1940.5, "stop_loss": 1908.2, "target": 2052.75, "quantity": 4, "risk_amount": 165.2, "quant_score": 74.8},
    {"symbol": "DLF.NS", "price": 662.0, "stop_loss": 638.1, "target": 728.4, "quantity": 7, "risk_amount": 180.6, "quant_score": 63.2}
]

cmd_test = [
    {"mcx_ticker": "CRUDEOILM", "expiry_month": "AUG 2026 FUTURES", "mcx_entry_price": 7599.7, "mcx_stop_loss": 7450.0, "mcx_target": 7975.0, "approx_margin": 13800.0, "quant_score": 60.0},
    {"mcx_ticker": "GOLDPETAL", "expiry_month": "AUG 2026 FUTURES", "mcx_entry_price": 14360.0, "mcx_stop_loss": 14190.0, "mcx_target": 14785.0, "approx_margin": 1328.25, "quant_score": 55.0}
]

print("Testing send_combined_clean_trade_cards()...")
res1 = send_combined_clean_trade_cards(eq_test, cmd_test)
print(f"Result: {res1}")

print("\nTesting send_eod_telegram_journal_summary()...")
send_eod_telegram_journal_summary()
