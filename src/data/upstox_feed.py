import os
import sys
import requests
import pandas as pd
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config import BASE_DIR

UPSTOX_ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN", "")

# Known Upstox Instrument Keys for MCX Mini/Micro Futures Contracts
UPSTOX_MCX_INSTRUMENT_KEYS = {
    "SILVERMIC": "MCX_FO|488788",    # SILVERMIC 31AUG26 FUT (1 Kg)
    "GOLDPETAL": "MCX_FO|562056",    # GOLDPETAL 31AUG26 FUT (1 Gram)
    "GOLDGUINEA": "MCX_FO|562055",   # GOLDGUINEA 31AUG26 FUT (8 Grams)
    "CRUDEOILM": "MCX_FO|565900",    # CRUDEOILM 21SEP26 FUT
    "NATGASMINI": "MCX_FO|568246"    # NATGASMINI 25SEP26 FUT
}

def fetch_upstox_live_ohlc(instrument_key: str) -> dict:
    """
    Fetches 100% exact live OHLC quote directly from Upstox V2 API.
    """
    if not UPSTOX_ACCESS_TOKEN:
        return {"error": "MISSING_TOKEN"}

    url = f"https://api.upstox.com/v2/market-quote/ohlc?symbol={instrument_key}&interval=1d"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {UPSTOX_ACCESS_TOKEN}"
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "success" and "data" in data:
                return {"status": "SUCCESS", "ohlc": data["data"]}
        return {"error": f"HTTP_{res.status_code}", "response": res.text}
    except Exception as e:
        return {"error": str(e)}

def fetch_upstox_historical_candles(instrument_key: str, interval: str = "day") -> pd.DataFrame:
    """
    Downloads historical candles directly from Upstox servers to compute 20 EMA, RSI, ATR.
    """
    if not UPSTOX_ACCESS_TOKEN:
        return pd.DataFrame()

    url = f"https://api.upstox.com/v2/historical-candle/{instrument_key}/{interval}"
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {UPSTOX_ACCESS_TOKEN}"
    }

    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            candles = data.get("data", {}).get("candles", [])
            if candles:
                # Upstox candle format: [timestamp, open, high, low, close, volume, open_interest]
                df = pd.DataFrame(candles, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume', 'OI'])
                df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                df = df.sort_values('Timestamp').reset_index(drop=True)
                return df
    except Exception as e:
        print(f"[UPSTOX FEED ERROR]: {e}")
        
    return pd.DataFrame()

if __name__ == "__main__":
    print("="*60)
    print(" TESTING UPSTOX DIRECT LIVE MARKET FEED MODULE")
    print("="*60)
    print(f"UPSTOX ACCESS TOKEN: {'CONFIGURED ✅' if UPSTOX_ACCESS_TOKEN else 'MISSING IN .env (PASTE TOKEN TO ACTIVATE) ⚠️'}")
    print("="*60)
