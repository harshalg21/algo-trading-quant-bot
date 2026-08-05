import sys
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DEFAULT_STOCK_UNIVERSE, ACCOUNT_EQUITY, MAX_RISK_PER_TRADE_PCT
from src.data.fetcher import fetch_stock_data
from src.risk.position_sizer import calculate_position_size
from src.alerts.telegram_bot import send_telegram_signal
from src.strategies.momentum_breakout import compute_sma, compute_rolling_max, compute_rsi, compute_atr

def scan_symbol_for_signal(symbol: str) -> dict:
    try:
        df = fetch_stock_data(symbol, period="1y", interval="1d")
        if len(df) < 200:
            return None

        close = df['Close'].to_numpy()
        high = df['High'].to_numpy()
        low = df['Low'].to_numpy()
        volume = df['Volume'].to_numpy()

        sma200 = compute_sma(close, 200)
        rolling_high = compute_rolling_max(high, 20)
        vol_sma = compute_sma(volume, 20)
        rsi = compute_rsi(close, 14)
        atr = compute_atr(high, low, close, 14)

        price = close[-1]
        is_uptrend = price > sma200[-1]
        is_breakout = price >= rolling_high[-1]
        is_high_vol = volume[-1] >= (vol_sma[-1] * 1.5)
        is_rsi_valid = 50 <= rsi[-1] <= 75

        if is_uptrend and is_breakout and is_high_vol and is_rsi_valid:
            atr_val = atr[-1]
            sl_price = price - (atr_val * 1.5)
            tp_price = price + (atr_val * 1.5 * 3.0)

            sizer = calculate_position_size(
                account_equity=ACCOUNT_EQUITY,
                risk_per_trade_pct=MAX_RISK_PER_TRADE_PCT,
                entry_price=price,
                stop_loss_price=sl_price
            )

            return {
                "symbol": symbol,
                "price": price,
                "stop_loss": round(sl_price, 2),
                "target": round(tp_price, 2),
                "quantity": sizer['quantity'],
                "risk_amount": sizer['max_risk_amount']
            }
    except Exception as e:
        print(f"Error scanning {symbol}: {e}")
        return None

def main():
    print("="*60)
    print("RUNNING DAILY SWING BREAKOUT SIGNAL SCANNER (NIFTY UNIVERSE)")
    print("="*60)
    
    signals_found = 0
    for symbol in DEFAULT_STOCK_UNIVERSE:
        sig = scan_symbol_for_signal(symbol)
        if sig:
            signals_found += 1
            print(f"\n[SIGNAL MATCH DETECTED]: {sig['symbol']}")
            send_telegram_signal(
                symbol=sig['symbol'],
                signal_type="BUY BREAKOUT",
                entry_price=sig['price'],
                stop_loss=sig['stop_loss'],
                target_price=sig['target'],
                quantity=sig['quantity'],
                risk_amount=sig['risk_amount']
            )

    if signals_found == 0:
        print("\nNo breakout signals met criteria today across the universe.")

if __name__ == "__main__":
    main()
