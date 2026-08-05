import json
import sys
import pandas as pd
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DEFAULT_STOCK_UNIVERSE, RESULTS_DIR
from src.data.fetcher import fetch_stock_data
from src.backtest.engine import run_single_backtest
from src.strategies.momentum_breakout import MomentumBreakoutStrategy, compute_sma, compute_rolling_max, compute_rsi, compute_atr

class NiftyRegimeBreakoutStrategy(MomentumBreakoutStrategy):
    volume_multiplier = 1.5
    risk_reward_ratio = 2.0
    atr_sl_multiplier = 2.5
    breakout_period = 20

    def init(self):
        super().init()
        # Track Nifty Bullish column if present
        if 'Nifty_Bullish' in self.data.df.columns:
            self.nifty_bullish = self.I(lambda: self.data.df['Nifty_Bullish'].to_numpy(), name="Nifty_Bullish")
        else:
            self.nifty_bullish = None

    def next(self):
        if len(self.data) < self.sma_period:
            return

        # Market Regime Filter: Only enter if Nifty 50 is bullish
        if self.nifty_bullish is not None and not self.nifty_bullish[-1]:
            return

        price = self.data.Close[-1]
        
        if not self.position:
            is_uptrend = price > self.sma200[-1]
            is_breakout = price >= self.rolling_high[-1]
            is_high_vol = self.data.Volume[-1] >= (self.vol_sma[-1] * self.volume_multiplier)
            is_rsi_valid = self.rsi_min <= self.rsi[-1] <= self.rsi_max

            if is_uptrend and is_breakout and is_high_vol and is_rsi_valid:
                atr_val = self.atr[-1]
                if np.isnan(atr_val) or atr_val <= 0:
                    return

                sl_price = price - (atr_val * self.atr_sl_multiplier)
                tp_price = price + (atr_val * self.atr_sl_multiplier * self.risk_reward_ratio)

                if sl_price < price and tp_price > price:
                    self.buy(sl=sl_price, tp=tp_price)

def run_nifty_filtered_experiment():
    print("="*70)
    print("RUNNING EXP 4: NIFTY 50 INDEX REGIME FILTER + 2.5x ATR SL")
    print("="*70)

    # Fetch Nifty 50 index data
    nifty_df = fetch_stock_data("^NSEI", period="2y")
    nifty_df['Nifty_EMA50'] = nifty_df['Close'].ewm(span=50, adjust=False).mean()
    nifty_df['Nifty_Bullish'] = nifty_df['Close'] > nifty_df['Nifty_EMA50']

    portfolio_results = []
    total_trades = 0
    winning_trades = 0
    total_returns = []
    drawdowns = []

    for symbol in DEFAULT_STOCK_UNIVERSE:
        try:
            df = fetch_stock_data(symbol, period="2y")
            
            # Align Nifty bullish filter with stock candles using pandas 3.0 ffill
            df = df.join(nifty_df[['Nifty_Bullish']], how='left').ffill()
            df['Nifty_Bullish'] = df['Nifty_Bullish'].astype(bool)
            
            metrics, stats = run_single_backtest(
                df,
                strategy_cls=NiftyRegimeBreakoutStrategy,
                cash=100000.0,
                commission=0.001
            )
            
            trades = metrics['Total_Trades']
            win_rate = metrics['Win_Rate_Pct']
            ret_pct = metrics['Return_Pct']
            max_dd = metrics['Max_Drawdown_Pct']

            wins = round((win_rate / 100.0) * trades)
            total_trades += trades
            winning_trades += wins
            total_returns.append(ret_pct)
            drawdowns.append(max_dd)

            print(f"[{symbol:<15}] Trades: {trades:<3} | Win Rate: {win_rate:>5.1f}% | Return: {ret_pct:>6.2f}% | Max DD: {max_dd:>6.2f}%")

        except Exception as e:
            print(f"[{symbol:<15}] Error: {e}")

    overall_win_rate = round((winning_trades / total_trades * 100.0), 2) if total_trades > 0 else 0.0
    avg_return = round(sum(total_returns) / len(total_returns), 2) if total_returns else 0.0
    worst_dd = round(min(drawdowns), 2) if drawdowns else 0.0

    print("\n" + "="*70)
    print("EXP 4 RESULTS (WITH NIFTY INDEX REGIME FILTER)")
    print("="*70)
    print(f"Total Trades Executed: {total_trades}")
    print(f"Overall Portfolio Win Rate: {overall_win_rate}%")
    print(f"Average Return Per Stock: {avg_return}%")
    print(f"Worst Single Stock Drawdown: {worst_dd}%")
    print("="*70)

if __name__ == "__main__":
    run_nifty_filtered_experiment()
