import argparse
import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.fetcher import fetch_stock_data
from src.backtest.engine import run_single_backtest
from src.strategies.momentum_breakout import MomentumBreakoutStrategy, EMAPullbackStrategy
from src.config import RESULTS_DIR

def main():
    parser = argparse.ArgumentParser(description="Run backtest for Indian stock market swing strategy.")
    parser.add_argument("--symbol", type=str, default="LT.NS", help="Ticker symbol (e.g. LT.NS)")
    parser.add_argument("--period", type=str, default="2y", help="Historical data period (e.g. 1y, 2y, 5y)")
    parser.add_argument("--strategy", type=str, default="pullback", choices=["breakout", "pullback"], help="Strategy model")
    parser.add_argument("--volume_mult", type=float, default=1.5, help="Volume multiplier for entry filter")
    parser.add_argument("--rr_ratio", type=float, default=3.0, help="Risk Reward Ratio")
    
    args = parser.parse_args()
    
    # Download data if not already cached
    df = fetch_stock_data(args.symbol, period=args.period)
    
    strategy_cls = EMAPullbackStrategy if args.strategy == "pullback" else MomentumBreakoutStrategy
    
    clean_symbol = args.symbol.replace(".NS", "")
    plot_file = str(RESULTS_DIR / f"{clean_symbol}_backtest.html")
    
    metrics, stats = run_single_backtest(
        df,
        strategy_cls=strategy_cls,
        plot_path=plot_file
    )
    
    print("\n" + "="*50)
    print(f"BACKTEST RESULTS SUMMARY ({args.symbol})")
    print("="*50)
    print(json.dumps(metrics, indent=2))
    print("="*50)
    print(f"Interactive HTML Report generated: {plot_file}")

if __name__ == "__main__":
    main()
