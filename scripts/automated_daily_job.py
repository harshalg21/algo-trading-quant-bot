import os
import sys

# Fix OpenBLAS Memory Allocation Error - MUST BE BEFORE PANDAS/NUMPY IMPORTS
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import requests
import pandas as pd
from datetime import datetime
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import ACCOUNT_EQUITY, MAX_RISK_PER_TRADE_PCT, MAX_OPEN_POSITIONS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
from src.data.fetcher import fetch_stock_data
from src.data.dynamic_universe import get_dynamic_top_universe
from src.risk.position_sizer import calculate_position_size
from src.risk.quant_scorer import calculate_quant_probability_score
from src.ai.macro_agent import evaluate_global_macro_risk
from src.alerts.telegram_bot import send_combined_clean_trade_cards
from src.database.db import get_open_positions
from src.database.journal import send_eod_telegram_journal_summary
from src.execution.upstox_sync import sync_upstox_live_portfolio
from src.strategies.momentum_breakout import compute_sma, compute_rsi, compute_atr
from src.strategies.multi_timeframe import check_multi_timeframe_alignment
from src.commodity.commodity_agent import run_commodity_agent_analysis

MAX_HOLDING_DAYS_LIMIT = 25  # Time-based exit limit
TOP_SIGNALS_LIMIT = 5        # Max candidate cards per day

def monitor_open_positions():
    print("\n--- STEP 1: MONITORING ACTIVE OPEN POSITIONS ---")
    active_positions = get_open_positions()
    if not active_positions:
        print("No active open positions currently being tracked in DB.")
        return 0, []

    open_symbols = [pos['symbol'] for pos in active_positions]
    return len(active_positions), open_symbols

def scan_top_5_high_probability_signals(open_positions_count: int, open_symbols: list) -> list:
    print("\n--- STEP 3: SCANNING & FILTERING TOP HIGH PROBABILITY SETUPS ONLY ---")

    if open_positions_count >= MAX_OPEN_POSITIONS:
        print(f"\n⚠️ MAX OPEN POSITIONS REACHED ({open_positions_count}/{MAX_OPEN_POSITIONS}). Pausing new Buy alerts.")
        return []

    active_universe = get_dynamic_top_universe(top_n=20)
    candidate_signals = []

    for symbol in active_universe:
        if symbol in open_symbols:
            continue

        try:
            df = fetch_stock_data(symbol, period="6mo", interval="1d")
            if len(df) < 50:
                continue

            close = df['Close'].to_numpy()
            high = df['High'].to_numpy()
            low = df['Low'].to_numpy()

            sma200 = compute_sma(close, 200) if len(close) >= 200 else compute_sma(close, len(close)-1)
            ema20 = compute_sma(close, 20)
            rsi = compute_rsi(close, 14)
            atr = compute_atr(high, low, close, 14)

            price = close[-1]
            last_low = low[-1]

            is_uptrend = price > sma200[-1]
            ema_val = ema20[-1]
            is_pullback = last_low <= (ema_val * 1.03) and price >= (ema_val * 0.97)
            is_rsi_dip = 38 <= rsi[-1] <= 65

            if is_uptrend and is_pullback and is_rsi_dip:
                stop_loss = price - (atr[-1] * 1.5)
                target1 = price + (atr[-1] * 1.5 * 1.5)  # 1.5R Scale-Out Target
                target_price = price + (atr[-1] * 1.5 * 2.5)  # 2.5R Final Target

                momentum_6m = ((price - close[0]) / close[0]) * 100.0 if len(close) > 0 else 0.0
                quant_score = calculate_quant_probability_score(
                    symbol=symbol,
                    price=price,
                    sma200=sma200[-1],
                    rsi=rsi[-1],
                    six_month_return=momentum_6m
                )

                mtf = check_multi_timeframe_alignment(symbol)
                quant_score += mtf['score_bonus']

                if quant_score >= 60.0:
                    pos_size = calculate_position_size(
                        account_equity=ACCOUNT_EQUITY,
                        risk_per_trade_pct=MAX_RISK_PER_TRADE_PCT,
                        entry_price=price,
                        stop_loss_price=stop_loss
                    )

                    candidate_signals.append({
                        "symbol": symbol,
                        "price": price,
                        "stop_loss": stop_loss,
                        "target1": target1,
                        "target": target_price,
                        "quantity": pos_size['quantity'],
                        "risk_amount": pos_size['max_risk_amount'],
                        "quant_score": quant_score,
                        "mtf_badge": mtf['badge']
                    })

        except Exception as e:
            print(f"Error scanning {symbol}: {e}")

    candidate_signals.sort(key=lambda x: x['quant_score'], reverse=True)
    top_signals = candidate_signals[:TOP_SIGNALS_LIMIT]
    return top_signals

def main():
    print("="*75)
    print(f" 🤖 AUTOMATED DAILY JOB EXECUTING ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print("="*75)
    
    # 0. Sync 100% Exact Live Portfolio & Positions Directly From Upstox Servers
    sync_upstox_live_portfolio()

    open_count, open_symbols = monitor_open_positions()
    
    # 1. Equity Swing Scan
    eq_signals = scan_top_5_high_probability_signals(open_positions_count=open_count, open_symbols=open_symbols)
    
    # 2. MCX Commodity Futures Scan
    cmd_signals = run_commodity_agent_analysis()
    
    # 3. Dispatch EXACTLY 1 COMBINED Telegram Message (Zero Duplicates!)
    send_combined_clean_trade_cards(eq_signals, cmd_signals)

    # 4. Dispatch Complete EOD Portfolio & Journal Summary Card to Telegram
    send_eod_telegram_journal_summary()
    
    print("\n" + "="*75)
    print(" ✅ AUTOMATED DAILY JOB COMPLETED SUCCESSFULLY.")
    print("="*75)

if __name__ == "__main__":
    main()
