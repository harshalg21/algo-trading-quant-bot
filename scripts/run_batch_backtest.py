import json
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DEFAULT_STOCK_UNIVERSE, RESULTS_DIR
from src.data.fetcher import fetch_stock_data
from src.backtest.engine import run_single_backtest
from src.strategies.momentum_breakout import MomentumBreakoutStrategy

def run_portfolio_backtest(
    symbols: list = None,
    period: str = "2y",
    volume_mult: float = 1.5,
    rr_ratio: float = 3.0,
    atr_sl_mult: float = 1.5,
    rsi_min: int = 50,
    rsi_max: int = 75
) -> dict:
    if symbols is None:
        symbols = DEFAULT_STOCK_UNIVERSE

    portfolio_results = []
    total_trades = 0
    total_winning_trades = 0
    total_net_return_pct = 0.0
    max_drawdowns = []

    print("="*65)
    print(f"RUNNING PORTFOLIO BATCH BACKTEST ({len(symbols)} STOCKS | PERIOD: {period})")
    print(f"Params: Volume Mult={volume_mult}x | RR={rr_ratio} | ATR SL Mult={atr_sl_mult}x")
    print("="*65)

    # Dynamically create Strategy class with custom hyperparameters
    CustomStrategy = type(
        "CustomStrategy",
        (MomentumBreakoutStrategy,),
        {
            "volume_multiplier": volume_mult,
            "risk_reward_ratio": rr_ratio,
            "atr_sl_multiplier": atr_sl_mult,
            "rsi_min": rsi_min,
            "rsi_max": rsi_max
        }
    )

    for symbol in symbols:
        try:
            df = fetch_stock_data(symbol, period=period)
            metrics, stats = run_single_backtest(
                df,
                strategy_cls=CustomStrategy,
                cash=100000.0,
                commission=0.001
            )

            trades = metrics['Total_Trades']
            win_rate = metrics['Win_Rate_Pct']
            ret_pct = metrics['Return_Pct']
            max_dd = metrics['Max_Drawdown_Pct']

            wins = round((win_rate / 100.0) * trades)
            total_trades += trades
            total_winning_trades += wins
            total_net_return_pct += ret_pct
            max_drawdowns.append(max_dd)

            portfolio_results.append({
                "Symbol": symbol,
                "Trades": trades,
                "Win_Rate_Pct": win_rate,
                "Return_Pct": ret_pct,
                "Max_Drawdown_Pct": max_dd,
                "Sharpe_Ratio": metrics['Sharpe_Ratio']
            })

            print(f"[{symbol:<15}] Trades: {trades:<3} | Win Rate: {win_rate:>5.1f}% | Return: {ret_pct:>6.2f}% | Max DD: {max_dd:>6.2f}%")

        except Exception as e:
            print(f"[{symbol:<15}] Skipped due to error: {e}")

    overall_win_rate = round((total_winning_trades / total_trades * 100.0), 2) if total_trades > 0 else 0.0
    avg_return_per_stock = round(total_net_return_pct / len(symbols), 2) if symbols else 0.0
    worst_drawdown = round(min(max_drawdowns), 2) if max_drawdowns else 0.0

    summary = {
        "Parameters": {
            "Volume_Multiplier": volume_mult,
            "Risk_Reward_Ratio": rr_ratio,
            "ATR_SL_Multiplier": atr_sl_mult,
            "RSI_Range": f"{rsi_min}-{rsi_max}"
        },
        "Portfolio_Summary": {
            "Total_Stocks_Tested": len(symbols),
            "Total_Trades_Executed": total_trades,
            "Overall_Win_Rate_Pct": overall_win_rate,
            "Average_Return_Per_Stock_Pct": avg_return_per_stock,
            "Worst_Single_Stock_Drawdown_Pct": worst_drawdown
        },
        "Stock_Breakdown": portfolio_results
    }

    # Save summary JSON
    summary_file = RESULTS_DIR / f"batch_backtest_vol{volume_mult}_rr{rr_ratio}.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)

    print("\n" + "="*65)
    print("AGGREGATED PORTFOLIO METRICS")
    print("="*65)
    print(json.dumps(summary["Portfolio_Summary"], indent=2))
    print(f"\nDetailed report saved to: {summary_file}")
    print("="*65)

    return summary

if __name__ == "__main__":
    run_portfolio_backtest()
