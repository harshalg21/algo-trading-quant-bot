import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
RESULTS_DIR = BASE_DIR / "results"

# Load environment variables explicitly from BASE_DIR/.env
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Ensure directories exist
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Risk Settings (Tailored for ₹20,000 Upstox Account)
ACCOUNT_EQUITY = float(os.getenv("ACCOUNT_EQUITY", "20000.0"))
MAX_RISK_PER_TRADE_PCT = float(os.getenv("MAX_RISK_PER_TRADE_PCT", "1.0"))
MAX_DAILY_DRAWDOWN_PCT = float(os.getenv("MAX_DAILY_DRAWDOWN_PCT", "3.0"))
MAX_OPEN_POSITIONS = int(os.getenv("MAX_OPEN_POSITIONS", "3"))

# API Keys
DHAN_CLIENT_ID = os.getenv("DHAN_CLIENT_ID", "")
DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN", "")

FYERS_APP_ID = os.getenv("FYERS_APP_ID", "")
FYERS_ACCESS_TOKEN = os.getenv("FYERS_ACCESS_TOKEN", "")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or "8885224492:AAGbba8SwrEJElElnULismAku2PmzvW_kx4"
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID") or "1186352880"
UPSTOX_ACCESS_TOKEN = os.getenv("UPSTOX_ACCESS_TOKEN") or "eyJ0eXAiOiJKV1QiLCJrZXlfaWQiOiJza192MS4wIiwiYWxnIjoiSFMyNTYifQ.eyJzdWIiOiIzR0FQWUYiLCJqdGkiOiI2YTcwNTgyMmE5ZTkyOTEyMzY3OTczMWMiLCJpc011bHRpQ2xpZW50IjpmYWxzZSwiaXNQbHVzUGxhbiI6dHJ1ZSwiaXNFeHRlbmRlZCI6dHJ1ZSwiaWF0IjoxNzg1NzQ3NDkwLCJpc3MiOiJ1ZGFwaS1nYXRld2F5LXNlcnZpY2UiLCJleHAiOjE4MTczMzA0MDB9.mvpj3mC8M1qlnSG74sym2TtvuRkW05rO-Xp3waNdewk"

TRADING_MODE = os.getenv("TRADING_MODE", "PAPER")

# Default Nifty 200 liquid stock tickers for swing trading backtesting
DEFAULT_STOCK_UNIVERSE = [
    "RELIANCE.NS", "HDFCBANK.NS", "ICICIBANK.NS", "INFY.NS", "TCS.NS",
    "BHARTIARTL.NS", "LT.NS", "SBIN.NS", "M&M.NS", "AXISBANK.NS",
    "ITC.NS", "SUNPHARMA.NS", "TITAN.NS", "KOTAKBANK.NS", "HCLTECH.NS",
    "NTPC.NS", "BAJFINANCE.NS", "ONGC.NS", "ULTRACEMCO.NS", "MARUTI.NS"
]
