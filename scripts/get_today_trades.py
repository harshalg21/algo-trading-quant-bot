import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DEFAULT_STOCK_UNIVERSE, ACCOUNT_EQUITY, MAX_RISK_PER_TRADE_PCT
from src.data.fetcher import fetch_stock_data
from src.risk.position_sizer import calculate_position_size
from src.strategies.momentum_breakout import compute_sma, compute_rsi, compute_atr

def scan_symbol_for_trade(symbol: str) -> dict:
    try:
        df = fetch_stock_data(symbol, period="1y", interval="1d")
        if len(df) < 200:
            return None

        close = df['Close'].to_numpy()
        high = df['High'].to_numpy()
        low = df['Low'].to_numpy()

        sma200 = compute_sma(close, 200)
        ema20 = compute_sma(close, 20)
        rsi = compute_rsi(close, 14)
        atr = compute_atr(high, low, close, 14)

        price = close[-1]
        last_low = low[-1]

        # Trend Pullback Setup Rules
        is_uptrend = price > sma200[-1]
        ema_val = ema20[-1]
        is_pullback = last_low <= (ema_val * 1.01) and price >= (ema_val * 0.98)
        is_rsi_dip = 40 <= rsi[-1] <= 55

        if is_uptrend and is_pullback and is_rsi_dip:
            atr_val = atr[-1]
            sl_price = price - (atr_val * 1.5)
            tp_price = price + (atr_val * 1.5 * 2.5)

            sizer = calculate_position_size(
                account_equity=ACCOUNT_EQUITY,
                risk_per_trade_pct=MAX_RISK_PER_TRADE_PCT,
                entry_price=price,
                stop_loss_price=sl_price
            )

            return {
                "symbol": symbol,
                "action": "BUY",
                "entry_price": round(price, 2),
                "stop_loss": round(sl_price, 2),
                "target_price": round(tp_price, 2),
                "quantity": sizer['quantity'],
                "max_risk_inr": sizer['max_risk_amount'],
                "est_holding_period": "3 to 15 Trading Days"
            }
    except Exception:
        return None

def main():
    print("="*75)
    print(" 🎯 DAILY ACTIONABLE TRADE CHEAT SHEET FOR BUSY DEVELOPERS")
    print(f" Account Capital: ₹{ACCOUNT_EQUITY:,.2f} | Risk Per Trade: {MAX_RISK_PER_TRADE_PCT}% (₹1,000)")
    print("="*75)

    actionable_trades = []
    for symbol in DEFAULT_STOCK_UNIVERSE:
        trade = scan_symbol_for_trade(symbol)
        if trade:
            actionable_trades.append(trade)

    if not actionable_trades:
        print("\n 🔍 NO ACTIVE ACTIONABLE TRADES TODAY.")
        print("    Why? Market condition criteria (Price > 200 SMA + Pullback to 20 EMA) not triggered.")
        print("    Recommendation: Stand by and check again tomorrow at 3:15 PM IST.\n")
        print("="*75)
        return

    print(f"\n Found {len(actionable_trades)} Actionable Trade Setup(s) Today:\n")
    
    for idx, t in enumerate(actionable_trades, 1):
        print(f"┌{'─'*65}┐")
        print(f"│ TRADE CARD #{idx}: {t['symbol']:<48} │")
        print(f"├{'─'*65}┤")
        print(f"│  • ACTION             : {t['action']} (Long Swing Trade)")
        print(f"│  • ENTRY PRICE        : ₹{t['entry_price']:<10.2f} (Buy at current market price)")
        print(f"│  • STOP LOSS          : ₹{t['stop_loss']:<10.2f} (Hard exit if price drops here)")
        print(f"│  • TARGET PRICE (2.5R): ₹{t['target_price']:<10.2f} (Take profit level)")
        print(f"│  • EXACT SHARES TO BUY: {t['quantity']:<10} (Calculated for ₹{t['max_risk_inr']} max risk)")
        print(f"│  • HOLDING PERIOD     : {t['est_holding_period']}")
        print(f"└{'─'*65}┘\n")

    print("="*75)
    print(" 💡 WHAT TO DO RIGHT NOW IN YOUR BROKER APP (DHAN / ZERODHA):")
    print(" 1. Open your Broker App (Dhan / Zerodha / Angel One).")
    print(" 2. Search for the Stock Symbol above.")
    print(" 3. Place a BUY Order for the exact number of shares specified.")
    print(" 4. Place a STOP LOSS (SL-M) order at the Stop Loss price.")
    print(" 5. Close your app! The system will automatically hit Target or Stop Loss.")
    print("="*75)

if __name__ == "__main__":
    main()
