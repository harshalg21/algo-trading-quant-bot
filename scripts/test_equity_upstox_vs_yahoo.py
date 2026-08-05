import sys
import yfinance as yf
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.fetcher import fetch_stock_data

def test_equity_comparison():
    print("="*60)
    print(" TESTING NSE EQUITY PRICES ON YAHOO VS UPSTOX")
    print("="*60)

    for sym in ["DLF.NS", "SUNPHARMA.NS", "SBIN.NS", "RELIANCE.NS"]:
        try:
            df = fetch_stock_data(sym, period="5d")
            last_close = df['Close'].iloc[-1]
            print(f"✅ {sym:<15} Yahoo/NSE Last Close = ₹{last_close:,.2f}")
        except Exception as e:
            print(f"Error {sym}: {e}")

if __name__ == "__main__":
    test_equity_comparison()
