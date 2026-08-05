import yfinance as yf
import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.strategies.momentum_breakout import compute_sma, compute_rsi, compute_atr

def run_detailed_backtest():
    universe = ["SUNPHARMA.NS", "DLF.NS", "TITAN.NS", "BAJFINANCE.NS", "TRENT.NS", "ADANIENT.NS", "EICHERMOT.NS", "ICICIBANK.NS"]
    
    total_trades = 0
    full_target2_wins = 0
    scaleout_target1_wins = 0
    losses = 0
    total_pnl_pct = 0.0

    for sym in universe:
        try:
            df = yf.Ticker(sym).history(period="2y", interval="1d")
            if len(df) < 200:
                continue

            close = df['Close'].to_numpy()
            high = df['High'].to_numpy()
            low = df['Low'].to_numpy()

            sma200 = compute_sma(close, 200)
            ema20 = compute_sma(close, 20)
            rsi = compute_rsi(close, 14)
            atr = compute_atr(high, low, close, 14)

            in_trade = False
            entry_p = 0.0
            sl_p = 0.0
            tp1_p = 0.0
            tp2_p = 0.0
            scaled_out = False

            for i in range(200, len(close)-1):
                price = close[i]
                
                if not in_trade:
                    is_uptrend = price > sma200[i]
                    is_exact_dip = low[i] <= (ema20[i] * 1.005) and price >= (ema20[i] * 0.985)
                    is_rsi_dip = 40 <= rsi[i] <= 56

                    if is_uptrend and is_exact_dip and is_rsi_dip:
                        in_trade = True
                        entry_p = price
                        risk = atr[i] * 1.5
                        sl_p = price - risk
                        tp1_p = price + (risk * 1.5)
                        tp2_p = price + (risk * 2.5)
                        scaled_out = False
                else:
                    if not scaled_out and high[i] >= tp1_p:
                        scaled_out = True
                        sl_p = entry_p  # Move SL to breakeven ($0 Risk)
                        scaleout_target1_wins += 1

                    if low[i] <= sl_p:
                        total_trades += 1
                        if scaled_out:
                            pnl = ((tp1_p - entry_p)/entry_p * 0.5) * 100.0  # Kept 50% profit
                        else:
                            pnl = ((sl_p - entry_p) / entry_p) * 100.0
                            losses += 1
                        total_pnl_pct += pnl
                        in_trade = False
                    elif high[i] >= tp2_p:
                        total_trades += 1
                        full_target2_wins += 1
                        pnl = ((tp2_p - entry_p) / entry_p) * 100.0
                        total_pnl_pct += pnl
                        in_trade = False
        except Exception:
            pass

    print("="*75)
    print(" 📊 DETAILED QUANTITATIVE BACKTEST BREAKDOWN (2-YEAR DATA)")
    print("="*75)
    print(f" • Total Trades Executed           : {total_trades}")
    print(f" • Full Target 2 (2.5R) Home-Runs  : {full_target2_wins} Trades")
    print(f" • Target 1 (1.5R) Scale-Out Wins  : {scaleout_target1_wins} Trades (Risk = ₹0)")
    print(f" • Small Controlled Losses          : {losses} Trades (Strict SL)")
    print(f" • Combined Positive Trade Rate     : {round((full_target2_wins + scaleout_target1_wins)/total_trades * 100, 1)}%")
    print(f" • TOTAL CUMULATIVE ACCOUNT RETURN : +{round(total_pnl_pct, 2)}% NET PROFIT")
    print("="*75)

if __name__ == "__main__":
    run_detailed_backtest()
