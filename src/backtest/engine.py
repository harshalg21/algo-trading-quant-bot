import json
import pandas as pd
from backtesting import Backtest
from src.strategies.momentum_breakout import MomentumBreakoutStrategy
from src.config import RESULTS_DIR

def run_single_backtest(
    df: pd.DataFrame,
    strategy_cls=MomentumBreakoutStrategy,
    cash: float = 100000.0,
    commission: float = 0.001,  # 0.1% brokerage + taxes
    plot_path: str = None,
    **kwargs
) -> dict:
    """
    Executes backtest on a single OHLCV DataFrame and returns formatted metrics JSON.
    """
    # Ensure correct index and column formatting
    df_clean = df.copy()
    if 'Date' in df_clean.columns:
        df_clean.set_index('Date', inplace=True)
        
    bt = Backtest(
        df_clean,
        strategy_cls,
        cash=cash,
        commission=commission,
        exclusive_orders=True
    )
    
    stats = bt.run(**kwargs)
    
    if plot_path:
        bt.plot(filename=plot_path, open_browser=False)
        
    metrics = {
        "Currency": "INR (₹)",
        "Start": str(stats['Start']),
        "End": str(stats['End']),
        "Duration": str(stats['Duration']),
        "Exposure_Time_Pct": round(float(stats['Exposure Time [%]']), 2),
        "Equity_Final_INR": f"₹{round(float(stats['Equity Final [$]']), 2):,}",
        "Equity_Peak_INR": f"₹{round(float(stats['Equity Peak [$]']), 2):,}",
        "Return_Pct": round(float(stats['Return [%]']), 2),
        "Buy_Hold_Return_Pct": round(float(stats['Buy & Hold Return [%]']), 2),
        "Max_Drawdown_Pct": round(float(stats['Max. Drawdown [%]']), 2),
        "Avg_Drawdown_Pct": round(float(stats['Avg. Drawdown [%]']), 2),
        "Total_Trades": int(stats['# Trades']),
        "Win_Rate_Pct": round(float(stats['Win Rate [%]']), 2) if not pd.isna(stats['Win Rate [%]']) else 0.0,
        "Best_Trade_Pct": round(float(stats['Best Trade [%]']), 2) if not pd.isna(stats['Best Trade [%]']) else 0.0,
        "Worst_Trade_Pct": round(float(stats['Worst Trade [%]']), 2) if not pd.isna(stats['Worst Trade [%]']) else 0.0,
        "Avg_Trade_Pct": round(float(stats['Avg. Trade [%]']), 2) if not pd.isna(stats['Avg. Trade [%]']) else 0.0,
        "Profit_Factor": round(float(stats['Profit Factor']), 2) if not pd.isna(stats['Profit Factor']) else 0.0,
        "Sharpe_Ratio": round(float(stats['Sharpe Ratio']), 2) if not pd.isna(stats['Sharpe Ratio']) else 0.0,
        "Sortino_Ratio": round(float(stats['Sortino Ratio']), 2) if not pd.isna(stats['Sortino Ratio']) else 0.0,
    }
    
    return metrics, stats
