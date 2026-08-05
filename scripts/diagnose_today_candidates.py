import os
import sys

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import yfinance as yf
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import ACCOUNT_EQUITY, MAX_RISK_PER_TRADE_PCT
from src.strategies.momentum_breakout import compute_sma, compute_rsi, compute_atr
from src.strategies.multi_timeframe import check_multi_timeframe_alignment
from src.risk.quant_scorer import calculate_quant_probability_score

def diagnose():
    print("="*75)
    print(" 🔍 DIAGNOSING TODAY'S CANDIDATE SIGNAL FILTERING")
    print("="*75)

    universe = ["SUNPHARMA.NS", "DLF.NS", "TITAN.NS", "BAJFINANCE.NS", "TRENT.NS", "ADANIENT.NS", "HAL.NS", "EICHERMOT.NS", "ADANIPORTS.NS", "ICICIBANK.NS"]
    for symbol in universe:
        try:
            df = yf.Ticker(symbol).history(period="6mo", interval="1d")
            if len(df) < 50:
                continue

            close = df['Close'].to_numpy()
            high = df['High'].to_numpy()
            low = df['Low'].to_numpy()

            sma200 = compute_sma(close, 200) if len(close) >= 200 else compute_sma(close, len(close)-1)
            ema20 = compute_sma(close, 20)
            rsi = compute_rsi(close, 14)

            price = close[-1]
            last_low = low[-1]

            is_uptrend = price > sma200[-1]
            ema_val = ema20[-1]
            is_pullback = last_low <= (ema_val * 1.04) and price >= (ema_val * 0.95)

            momentum_6m = ((price - close[0]) / close[0]) * 100.0 if len(close) > 0 else 0.0
            quant_score = calculate_quant_probability_score(symbol, price, sma200[-1], rsi[-1], momentum_6m)
            mtf = check_multi_timeframe_alignment(symbol)
            quant_score += mtf['score_bonus']

            print(f" • {symbol:<15}: Price=₹{price:,.2f} | 20EMA=₹{ema_val:,.2f} | RSI={rsi[-1]:.1f} | Score={quant_score:.1f} | Uptrend={is_uptrend} | Pullback={is_pullback}")

        except Exception as e:
            print(f"Error checking {symbol}: {e}")

if __name__ == "__main__":
    diagnose()
