import json
import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DEFAULT_STOCK_UNIVERSE, RESULTS_DIR
from src.data.fetcher import fetch_stock_data
from src.backtest.engine import run_single_backtest
from src.strategies.momentum_breakout import MomentumBreakoutStrategy, compute_sma, compute_rsi, compute_atr

class EMAPullbackStrategy(MomentumBreakoutStrategy):
    ema_period = 20
    sma_period = 200
    atr_sl_multiplier = 1.5
    risk_reward_ratio = 2.5

    def init(self):
        close = self.data.Close
        high = self.data.High
        low = self.data.Low

        self.sma200 = self.I(compute_sma, close, self.sma_period)
        self.ema20 = self.I(compute_sma, close, self.ema_period)
        self.rsi = self.I(compute_rsi, close, 14)
        self.atr = self.I(compute_atr, high, low, close, 14)

    def next(self):
        if len(self.data) < self.sma_period:
            return

        price = self.data.Close[-1]
        low = self.data.Low[-1]

        if not self.position:
            # 1. Major trend is Bullish (Price > 200 SMA)
            is_uptrend = price > self.sma200[-1]
            
            # 2. Pullback / Dip to 20 EMA (Low touches 20 EMA or close near 20 EMA)
            ema_val = self.ema20[-1]
            is_pullback = low <= (ema_val * 1.01) and price >= (ema_val * 0.98)
            
            # 3. RSI Cooldown (40 <= RSI <= 55)
            is_rsi_dip = 40 <= self.rsi[-1] <= 55

            if is_uptrend and is_pullback and is_rsi_dip:
                atr_val = self.atr[-1]
                if np.isnan(atr_val) or atr_val <= 0:
                    return

                sl_price = price - (atr_val * self.atr_sl_multiplier)
                tp_price = price + (atr_val * self.atr_sl_multiplier * self.risk_reward_ratio)

                if sl_price < price and tp_price > price:
                    self.buy(sl=sl_price, tp=tp_price)

def run_pullback_backtest():
    print("="*70)
    print("RUNNING EXP 6: TREND PULLBACK / DIP BUYING STRATEGY")
    print("="*70)

    portfolio_results = []
    total_trades = 0
    winning_trades = 0
    total_returns = []
    drawdowns = []

    for symbol in DEFAULT_STOCK_UNIVERSE:
        try:
            df = fetch_stock_data(symbol, period="2y")
            metrics, stats = run_single_backtest(df, strategy_cls=EMAPullbackStrategy, cash=100000.0, commission=0.001)

            trades = metrics['Total_Trades']
            win_rate = metrics['Win_Rate_Pct']
            ret_pct = metrics['Return_Pct']
            max_dd = metrics['Max_Drawdown_Pct']

            wins = round((win_rate / 100.0) * trades)
            total_trades += trades
            winning_trades += wins
            total_returns.append(ret_pct)
            drawdowns.append(max_dd)

            print(f"[{symbol:<15}] Trades: {trades:<3} | Win Rate: {win_rate:>5.1f}% | Return: {ret_pct:>+6.2f}% | Max DD: {max_dd:>6.2f}%")

        except Exception as e:
            print(f"[{symbol:<15}] Error: {e}")

    overall_win_rate = round((winning_trades / total_trades * 100.0), 2) if total_trades > 0 else 0.0
    avg_return = round(sum(total_returns) / len(total_returns), 2) if total_returns else 0.0
    worst_dd = round(min(drawdowns), 2) if drawdowns else 0.0

    print("\n" + "="*70)
    print("EXP 6 RESULTS (TREND PULLBACK STRATEGY)")
    print("="*70)
    print(f"Total Trades Executed: {total_trades}")
    print(f"Overall Portfolio Win Rate: {overall_win_rate}%")
    print(f"Average Return Per Stock: {avg_return:+}%")
    print(f"Worst Single Stock Drawdown: {worst_dd}%")
    print("="*70)

if __name__ == "__main__":
    run_pullback_backtest()
