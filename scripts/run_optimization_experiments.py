import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DEFAULT_STOCK_UNIVERSE, RESULTS_DIR
from src.data.fetcher import fetch_stock_data
from src.backtest.engine import run_single_backtest
from src.strategies.momentum_breakout import MomentumBreakoutStrategy, compute_sma, compute_rolling_max, compute_rsi, compute_atr

def run_experiment_variation(name: str, volume_mult: float, rr_ratio: float, atr_sl_mult: float, breakout_period: int):
    print(f"\n--- Running Experiment: {name} ---")
    
    CustomStrategy = type(
        "CustomStrategy",
        (MomentumBreakoutStrategy,),
        {
            "volume_multiplier": volume_mult,
            "risk_reward_ratio": rr_ratio,
            "atr_sl_multiplier": atr_sl_mult,
            "breakout_period": breakout_period
        }
    )
    
    total_trades = 0
    winning_trades = 0
    total_returns = []
    drawdowns = []

    for symbol in DEFAULT_STOCK_UNIVERSE:
        try:
            df = fetch_stock_data(symbol, period="2y")
            metrics, stats = run_single_backtest(df, strategy_cls=CustomStrategy, cash=100000.0, commission=0.001)
            
            trades = metrics['Total_Trades']
            win_rate = metrics['Win_Rate_Pct']
            ret_pct = metrics['Return_Pct']
            max_dd = metrics['Max_Drawdown_Pct']
            
            wins = round((win_rate / 100.0) * trades)
            total_trades += trades
            winning_trades += wins
            total_returns.append(ret_pct)
            drawdowns.append(max_dd)
        except Exception:
            pass

    overall_win_rate = round((winning_trades / total_trades * 100.0), 2) if total_trades > 0 else 0.0
    avg_return = round(sum(total_returns) / len(total_returns), 2) if total_returns else 0.0
    worst_dd = round(min(drawdowns), 2) if drawdowns else 0.0

    return {
        "Experiment_Name": name,
        "Total_Trades": total_trades,
        "Win_Rate_Pct": overall_win_rate,
        "Avg_Return_Per_Stock_Pct": avg_return,
        "Worst_Drawdown_Pct": worst_dd
    }

def main():
    print("="*65)
    print("AGENTIC STRATEGY OPTIMIZATION LAB (NSE SWING TRADING)")
    print("="*65)

    experiments = [
        {"name": "Baseline (20d High, 1.5x Vol, 1.5x ATR SL, 1:3 RR)", "vol": 1.5, "rr": 3.0, "atr_sl": 1.5, "breakout": 20},
        {"name": "Exp 1: Wider SL (2.5x ATR SL, 1:2 RR)", "vol": 1.5, "rr": 2.0, "atr_sl": 2.5, "breakout": 20},
        {"name": "Exp 2: 55-Day Major High Breakout (2.0x ATR SL, 1:2.5 RR)", "vol": 1.2, "rr": 2.5, "atr_sl": 2.0, "breakout": 55},
        {"name": "Exp 3: Strict Institutional Filter (55d High, 2.0x Vol, 2.5x ATR SL, 1:3 RR)", "vol": 2.0, "rr": 3.0, "atr_sl": 2.5, "breakout": 55},
    ]

    leaderboard = []
    for exp in experiments:
        res = run_experiment_variation(exp['name'], exp['vol'], exp['rr'], exp['atr_sl'], exp['breakout'])
        leaderboard.append(res)

    print("\n" + "="*70)
    print("OPTIMIZATION LEADERBOARD")
    print("="*70)
    print(f"{'Experiment Name':<42} | {'Trades':<6} | {'Win Rate':<8} | {'Avg Return':<10} | {'Worst DD':<8}")
    print("-" * 70)
    for l in leaderboard:
        print(f"{l['Experiment_Name']:<42} | {l['Total_Trades']:<6} | {l['Win_Rate_Pct']:>6.1f}% | {l['Avg_Return_Per_Stock_Pct']:>8.2f}% | {l['Worst_Drawdown_Pct']:>7.2f}%")
    print("="*70)

if __name__ == "__main__":
    main()
