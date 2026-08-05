import pandas as pd
import numpy as np

# Historical win rate weights from our 2-year backtests
HISTORICAL_STOCK_WIN_RATES = {
    "SBIN.NS": 62.5,
    "LT.NS": 55.6,
    "INFY.NS": 100.0,
    "TITAN.NS": 38.5,
    "AXISBANK.NS": 40.0,
    "M&M.NS": 37.5,
    "BHARTIARTL.NS": 33.3,
    "RELIANCE.NS": 33.3,
    "HDFCBANK.NS": 33.3,
    "DLF.NS": 45.0,
    "TRENT.NS": 50.0,
    "HAL.NS": 48.0,
    "ADANIENT.NS": 42.0
}

def calculate_quant_probability_score(
    symbol: str,
    price: float,
    sma200: float,
    rsi: float,
    six_month_return: float
) -> float:
    """
    Calculates a Multi-Factor Probability Score (0 to 100) for a trade setup:
    1. 6-Month Relative Momentum (Max 30 Pts)
    2. Historical Stock Backtest Win Rate (Max 30 Pts)
    3. Structural Uptrend Distance above 200 SMA (Max 20 Pts)
    4. RSI Dip Cooldown Perfection (Max 20 Pts)
    """
    score = 0.0

    # 1. 6-Month Relative Momentum (Max 30 Pts)
    if six_month_return > 30:
        score += 30.0
    elif six_month_return > 15:
        score += 22.5
    elif six_month_return > 5:
        score += 15.0
    elif six_month_return > 0:
        score += 7.5

    # 2. Historical Stock Backtest Win Rate (Max 30 Pts)
    hist_win_rate = HISTORICAL_STOCK_WIN_RATES.get(symbol, 35.0)
    score += min(30.0, (hist_win_rate / 100.0) * 35.0)

    # 3. Structural Uptrend Distance (Price > 200 SMA) (Max 20 Pts)
    if sma200 > 0:
        dist_pct = ((price - sma200) / sma200) * 100.0
        if 2.0 <= dist_pct <= 25.0:
            score += 20.0  # Healthy trend
        elif dist_pct > 25.0:
            score += 12.0  # Slightly extended
        elif dist_pct > 0:
            score += 8.0

    # 4. RSI Dip Cooldown Perfection (Max 20 Pts)
    if 42 <= rsi <= 52:
        score += 20.0  # Perfect RSI Dip Zone
    elif 40 <= rsi <= 55:
        score += 12.0

    return round(min(100.0, score), 1)
