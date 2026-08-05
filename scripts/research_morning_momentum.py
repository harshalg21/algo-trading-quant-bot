import sys
import json
import yfinance as yf
import pandas as pd
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ai.macro_agent import evaluate_global_macro_risk
from src.data.fetcher import fetch_stock_data

def get_live_market_perspective():
    print("="*75)
    print(" 🌅 LIVE MONDAY MORNING MARKET PERSPECTIVE (11:00 AM IST)")
    print("="*75)

    # 1. Global Macro Risk Assessment
    macro = evaluate_global_macro_risk()
    print(f"\n🌍 GLOBAL MACRO STATUS: {macro['risk_level']}")
    print(f" • India VIX (^INDIAVIX)  : {macro['india_vix']} (Panic Threshold: > 22)")
    print(f" • US S&P 500 (^GSPC)     : {macro['spx_change_pct']:+.2f}%")
    print(f" • Brent Crude Oil (BZ=F) : {macro['crude_change_pct']:+.2f}%")

    # 2. Nifty 50 Benchmark Live Status
    try:
        nifty = yf.Ticker("^NSEI").history(period="5d", interval="1m")
        if not nifty.empty:
            open_p = nifty['Open'].iloc[0]
            curr_p = nifty['Close'].iloc[-1]
            high_p = nifty['High'].max()
            low_p = nifty['Low'].min()
            chg_pct = ((curr_p - open_p) / open_p) * 100.0
            print(f"\n🇮🇳 NIFTY 50 LIVE BENCHMARK:")
            print(f" • Open: ₹{open_p:,.2f} | Current: ₹{curr_p:,.2f} ({chg_pct:+.2f}%)")
            print(f" • Morning High: ₹{high_p:,.2f} | Morning Low: ₹{low_p:,.2f}")
    except Exception as e:
        print(f"Could not fetch live Nifty intraday: {e}")

def explore_morning_momentum_stocks():
    print("\n" + "="*75)
    print(" 🚀 MORNING MOMENTUM SCANNER (Nifty 200 Momentum Leaders Today)")
    print("="*75)

    symbols = [
        "ADANIENT.NS", "BAJFINANCE.NS", "TITAN.NS", "SUNPHARMA.NS", "ADANIPORTS.NS",
        "TRENT.NS", "EICHERMOT.NS", "HAL.NS", "DLF.NS", "POWERGRID.NS", "ICICIBANK.NS",
        "SBIN.NS", "BHARTIARTL.NS", "LT.NS", "RELIANCE.NS", "INFY.NS", "TCS.NS"
    ]

    gainers = []
    for sym in symbols:
        try:
            df = yf.Ticker(sym).history(period="2d", interval="15m")
            if len(df) >= 4:
                today_df = df.iloc[-4:]  # Morning 9:15 - 10:15 AM candles
                first_15m_high = today_df['High'].iloc[0]
                curr_price = today_df['Close'].iloc[-1]
                gap_or_gain = ((curr_price - today_df['Open'].iloc[0]) / today_df['Open'].iloc[0]) * 100.0

                # Morning Momentum Breakout Rule: Current price > First 15m High & Positive Gain
                is_breakout = curr_price > first_15m_high
                
                gainers.append({
                    "symbol": sym,
                    "gain_pct": round(gap_or_gain, 2),
                    "curr_price": round(curr_price, 2),
                    "breakout": "🔥 15M HIGH BREAKOUT" if is_breakout else "HOLDING RANGE"
                })
        except Exception:
            pass

    gainers.sort(key=lambda x: x['gain_pct'], reverse=True)
    
    print(f"\nTop Morning Momentum Movers Today:")
    for idx, g in enumerate(gainers[:7], 1):
        print(f" {idx}. {g['symbol']:<15} | Gain: {g['gain_pct']:+6.2f}% | Price: ₹{g['curr_price']:<8.2f} | Status: {g['breakout']}")

if __name__ == "__main__":
    get_live_market_perspective()
    explore_morning_momentum_stocks()
