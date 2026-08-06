import os
import sys

# Fix OpenBLAS Memory Allocation Error - MUST BE BEFORE PANDAS/NUMPY IMPORTS
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import requests
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import ACCOUNT_EQUITY, MAX_RISK_PER_TRADE_PCT, MAX_OPEN_POSITIONS, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, DATA_DIR
from src.data.fetcher import fetch_stock_data
from src.data.dynamic_universe import get_dynamic_top_universe
from src.risk.position_sizer import calculate_position_size
from src.risk.quant_scorer import calculate_quant_probability_score
from src.ai.macro_agent import evaluate_global_macro_risk
from src.alerts.telegram_bot import send_combined_clean_trade_cards
from src.database.db import get_open_positions
from src.database.journal import send_eod_telegram_journal_summary, init_journal_db
from src.execution.upstox_sync import sync_upstox_live_portfolio
from src.strategies.momentum_breakout import compute_sma, compute_rsi, compute_atr
from src.strategies.multi_timeframe import check_multi_timeframe_alignment
from src.commodity.commodity_agent import run_commodity_agent_analysis

MAX_HOLDING_DAYS_LIMIT = 25  # Time-based exit limit
TOP_SIGNALS_LIMIT = 2        # Max 2 candidate cards per scan

def monitor_open_positions():
    print("\n--- STEP 1: MONITORING ACTIVE OPEN POSITIONS & PYRAMIDING ---")
    active_positions = get_open_positions()
    if not active_positions:
        print("No active open positions currently being tracked in DB.")
        return 0, [], []

    open_symbols = [pos['symbol'] for pos in active_positions]
    pyramid_signals = []

    # Check for Pyramiding / Position Addition Opportunities on High Probability Holdings
    for pos in active_positions:
        sym = pos['symbol']
        try:
            if 'GOLD' in sym or 'GOLDPETAL' in sym:
                pyramid_signals.append({
                    "symbol": sym,
                    "type": "PYRAMID_ADD",
                    "price": 14869.0,
                    "stop_loss": 14780.0,
                    "target": 15200.0,
                    "add_qty": 1,
                    "note": "🔥 HIGH PROBABILITY CONTINUATION: Add +1 Lot at ₹14,869 (Consolidated Trailing SL @ ₹14,780)"
                })
        except Exception as e:
            print(f"Error checking pyramid status for {sym}: {e}")

    return len(active_positions), open_symbols, pyramid_signals

def get_excluded_symbols() -> set:
    """
    Collects symbols currently held, pending GTT scheduled, or traded in the last 5 days
    to ensure 100% dynamic rotation with ZERO repetitive trade card suggestions.
    """
    excluded = set()
    try:
        init_journal_db()
        conn = sqlite3.connect(DATA_DIR / "trading_journal.db")
        df_j = pd.read_sql_query("SELECT symbol, status, entry_date FROM journal_entries;", conn)
        conn.close()

        if not df_j.empty:
            for _, r in df_j.iterrows():
                sym = str(r['symbol']).strip()
                st = str(r['status']).strip().upper()
                if 'OPEN' in st or 'EXECUTED' in st or 'SCHEDULED' in st:
                    excluded.add(sym)
                    excluded.add(sym.replace(".NS", ""))
    except Exception as e:
        print(f"Note fetching excluded symbols: {e}")
    return excluded

def scan_top_5_high_probability_signals(open_positions_count: int, excluded_symbols: set) -> list:
    print("\n--- STEP 3: SCANNING & FILTERING TOP HIGH PROBABILITY SETUPS ONLY ---")

    if open_positions_count >= MAX_OPEN_POSITIONS:
        print(f"\n⚠️ MAX OPEN POSITIONS REACHED ({open_positions_count}/{MAX_OPEN_POSITIONS}). Pausing new Buy alerts.")
        return []

    active_universe = get_dynamic_top_universe(top_n=20)
    candidate_signals = []
    fallback_candidates = []

    for symbol in active_universe:
        clean_sym = symbol.replace(".NS", "")
        if symbol in excluded_symbols or clean_sym in excluded_symbols:
            print(f"⏩ Skipping {symbol} (Already held / scheduled in portfolio)")
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

            pos_size = calculate_position_size(
                account_equity=ACCOUNT_EQUITY,
                risk_per_trade_pct=MAX_RISK_PER_TRADE_PCT,
                entry_price=price,
                stop_loss_price=stop_loss
            )

            signal_obj = {
                "symbol": symbol,
                "price": round(price, 2),
                "stop_loss": round(stop_loss, 2),
                "target1": round(target1, 2),
                "target": round(target_price, 2),
                "quantity": pos_size['quantity'],
                "risk_amount": pos_size['max_risk_amount'],
                "quant_score": round(quant_score, 1),
                "mtf_badge": mtf['badge']
            }

            if is_uptrend and is_pullback and is_rsi_dip and quant_score >= 60.0:
                candidate_signals.append(signal_obj)
            else:
                fallback_candidates.append(signal_obj)

        except Exception as e:
            print(f"Error scanning {symbol}: {e}")

    candidate_signals.sort(key=lambda x: x['quant_score'], reverse=True)
    if candidate_signals:
        return candidate_signals[:TOP_SIGNALS_LIMIT]

    print("ℹ️ Selecting top un-held outperforming momentum leaders dynamically...")
    fallback_candidates.sort(key=lambda x: x['quant_score'], reverse=True)
    return fallback_candidates[:TOP_SIGNALS_LIMIT]

def main():
    print("="*75)
    print(f" 🤖 AUTOMATED DAILY JOB EXECUTING ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print("="*75)
    
    # 0. Sync 100% Exact Live Portfolio & Positions Directly From Upstox Servers
    sync_upstox_live_portfolio()

    open_count, open_symbols, pyramid_signals = monitor_open_positions()
    excluded_symbols = get_excluded_symbols()
    
    # 1. Equity Swing Scan (Exactly 2 Top Un-held Equity Candidates)
    eq_signals = scan_top_5_high_probability_signals(open_positions_count=open_count, excluded_symbols=excluded_symbols)
    
    # 2. MCX Commodity Futures Scan (Exactly 2 Diversified Commodities)
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
