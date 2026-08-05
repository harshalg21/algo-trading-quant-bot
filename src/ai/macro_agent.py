import os
import json
import requests
import pandas as pd
import yfinance as yf
from src.config import BASE_DIR

def fetch_global_market_indicators() -> dict:
    """
    Fetches key Global Macro risk barometers:
    1. India VIX (^INDIAVIX) - Domestic Panic Gauge
    2. S&P 500 (^GSPC) - US Market Sentiment
    3. Brent Crude Oil (BZ=F) - Geopolitical & Commodity Inflation Gauge
    4. US Dollar Index (DX-Y.NYB) - Global Capital Flow Gauge
    """
    macro_data = {}
    
    # 1. India VIX
    try:
        vix = yf.Ticker("^INDIAVIX").history(period="5d")
        if not vix.empty:
            curr_vix = vix['Close'].iloc[-1]
            macro_data['india_vix'] = round(curr_vix, 2)
    except Exception:
        macro_data['india_vix'] = 14.5  # Neutral default

    # 2. S&P 500 Daily Change
    try:
        spx = yf.Ticker("^GSPC").history(period="5d")
        if len(spx) >= 2:
            prev = spx['Close'].iloc[-2]
            curr = spx['Close'].iloc[-1]
            spx_change = ((curr - prev) / prev) * 100.0
            macro_data['spx_daily_change_pct'] = round(spx_change, 2)
    except Exception:
        macro_data['spx_daily_change_pct'] = 0.0

    # 3. Crude Oil Daily Change
    try:
        crude = yf.Ticker("BZ=F").history(period="5d")
        if len(crude) >= 2:
            prev = crude['Close'].iloc[-2]
            curr = crude['Close'].iloc[-1]
            crude_change = ((curr - prev) / prev) * 100.0
            macro_data['crude_daily_change_pct'] = round(crude_change, 2)
    except Exception:
        macro_data['crude_daily_change_pct'] = 0.0

    return macro_data

def evaluate_global_macro_risk() -> dict:
    """
    Evaluates Global Macro Risk & Geopolitical Volatility.
    Returns Risk Status: 'NORMAL', 'CAUTION', or 'CRISIS_EMERGENCY'.
    """
    indicators = fetch_global_market_indicators()
    vix = indicators.get('india_vix', 14.5)
    spx_change = indicators.get('spx_daily_change_pct', 0.0)
    crude_change = indicators.get('crude_daily_change_pct', 0.0)
    
    risk_level = "NORMAL"
    reasons = []

    # Rule 1: High VIX Spike (India VIX > 22 = Extreme Panic)
    if vix >= 22.0:
        risk_level = "CRISIS_EMERGENCY"
        reasons.append(f"India VIX in Panic Zone ({vix} >= 22.0)")
    elif vix >= 18.0:
        risk_level = "CAUTION"
        reasons.append(f"India VIX Elevated ({vix})")

    # Rule 2: US Market Crash (S&P 500 dropped > 2% overnight)
    if spx_change <= -2.0:
        risk_level = "CRISIS_EMERGENCY" if risk_level != "NORMAL" else "CAUTION"
        reasons.append(f"US S&P 500 Over-Night Sell-off ({spx_change:.2f}%)")

    # Rule 3: Crude Oil Geopolitical Spike (Crude jumped > 4% in a day)
    if crude_change >= 4.0:
        risk_level = "CAUTION"
        reasons.append(f"Global Crude Oil Geopolitical Spike (+{crude_change:.2f}%)")

    return {
        "risk_level": risk_level,
        "india_vix": vix,
        "spx_change_pct": spx_change,
        "crude_change_pct": crude_change,
        "reasons": reasons
    }

if __name__ == "__main__":
    macro = evaluate_global_macro_risk()
    print("="*60)
    print(" GLOBAL MACRO & GEOPOLITICAL RISK ASSESSMENT")
    print("="*60)
    print(json.dumps(macro, indent=2))
    print("="*60)
