import sys
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.data.fetcher import fetch_stock_data
from src.data.dynamic_universe import get_dynamic_top_universe
from src.backtest.engine import run_single_backtest
from src.strategies.momentum_breakout import EMAPullbackStrategy
from src.config import RESULTS_DIR

print("="*75)
print(" 🚀 COMPREHENSIVE PORTFOLIO BACKTEST ENGINE (NSE REAL DATA)")
print("="*75)

# 1. Fetch Dynamic Universe
universe = get_dynamic_top_universe(top_n=15)
print(f"\nScanning & Backtesting Universe ({len(universe)} NSE Leaders): {universe}\n")

all_metrics = []
portfolio_total_trades = 0
portfolio_winning_trades = 0
portfolio_gross_profit = 0.0
portfolio_gross_loss = 0.0
initial_account_cash = 20000.0

for symbol in universe:
    try:
        df = fetch_stock_data(symbol, period="2y", interval="1d")
        if len(df) < 100:
            print(f"⏩ Skipping {symbol} (Insufficient data)")
            continue

        metrics, stats = run_single_backtest(
            df,
            strategy_cls=EMAPullbackStrategy,
            cash=initial_account_cash,
            commission=0.001  # 0.1% Brokerage + STT
        )

        n_trades = int(stats['# Trades'])
        win_rate = float(stats['Win Rate [%]']) if not pd.isna(stats['Win Rate [%]']) else 0.0
        ret_pct = float(stats['Return [%]']) if not pd.isna(stats['Return [%]']) else 0.0
        final_eq = float(stats['Equity Final [$]']) if not pd.isna(stats['Equity Final [$]']) else initial_account_cash
        pnl_inr = final_eq - initial_account_cash

        wins = int(n_trades * (win_rate / 100.0))
        losses = n_trades - wins

        portfolio_total_trades += n_trades
        portfolio_winning_trades += wins

        if pnl_inr > 0:
            portfolio_gross_profit += pnl_inr
        else:
            portfolio_gross_loss += abs(pnl_inr)

        all_metrics.append({
            "Symbol": symbol,
            "Trades": n_trades,
            "Win_Rate_Pct": round(win_rate, 2),
            "Return_Pct": round(ret_pct, 2),
            "Final_Equity_INR": round(final_eq, 2),
            "PnL_INR": round(pnl_inr, 2),
            "Max_Drawdown_Pct": round(float(stats['Max. Drawdown [%]']), 2) if not pd.isna(stats['Max. Drawdown [%]']) else 0.0,
            "Sharpe": round(float(stats['Sharpe Ratio']), 2) if not pd.isna(stats['Sharpe Ratio']) else 0.0
        })

        print(f" • {symbol:<15} | Trades: {n_trades:2d} | Win Rate: {win_rate:5.1f}% | Return: {ret_pct:+6.2f}% | PnL: ₹{pnl_inr:+8.2f}")

    except Exception as e:
        print(f"Error backtesting {symbol}: {e}")

# Portfolio Summary Calculations
overall_win_rate = (portfolio_winning_trades / portfolio_total_trades * 100.0) if portfolio_total_trades > 0 else 0.0
overall_profit_factor = (portfolio_gross_profit / portfolio_gross_loss) if portfolio_gross_loss > 0 else 99.0
net_portfolio_pnl = portfolio_gross_profit - portfolio_gross_loss
portfolio_return_pct = (net_portfolio_pnl / 20000.0) * 100.0

summary_report = {
    "Initial_Account_Equity_INR": 20000.0,
    "Final_Portfolio_Equity_INR": round(20000.0 + net_portfolio_pnl, 2),
    "Net_Portfolio_PnL_INR": round(net_portfolio_pnl, 2),
    "Net_Portfolio_Return_Pct": round(portfolio_return_pct, 2),
    "Total_Trades_Executed": portfolio_total_trades,
    "Winning_Trades": portfolio_winning_trades,
    "Overall_Win_Rate_Pct": round(overall_win_rate, 2),
    "Overall_Profit_Factor": round(overall_profit_factor, 2),
    "Individual_Stock_Results": all_metrics
}

output_json_path = RESULTS_DIR / "real_nse_portfolio_backtest_2y.json"
with open(output_json_path, "w") as f:
    json.dump(summary_report, f, indent=2)

print("\n" + "="*75)
print(" 📊 PORTFOLIO BACKTEST SUMMARY (2-YEAR REAL NSE DATA)")
print("="*75)
print(f" • Starting Capital       : ₹20,000.00")
print(f" • Final Capital          : ₹{20000.0 + net_portfolio_pnl:,.2f}")
print(f" • Net Profit (INR)       : ₹{net_portfolio_pnl:+,.2f}")
print(f" • Net Return (%)         : {portfolio_return_pct:+.2f}%")
print(f" • Overall Win Rate       : {overall_win_rate:.2f}%")
print(f" • Overall Profit Factor  : {overall_profit_factor:.2f}")
print(f" • Total Trades Executed  : {portfolio_total_trades}")
print("="*75)
print(f"Detailed JSON results saved to: {output_json_path}")
