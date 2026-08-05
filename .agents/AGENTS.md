# Workspace Rules for AlgoTrading AI Agent & Strategy Lab

## 1. Core Principles
- **Risk First**: Every strategy MUST enforce a strict Stop-Loss (e.g., $1.5 \times \text{ATR}$ or recent swing low) and calculated position sizing based on $1\%$ account risk per trade. Never remove stop-loss logic.
- **Data Integrity**: Standardize all OHLCV DataFrames with columns `['Open', 'High', 'Low', 'Close', 'Volume']` indexed by DateTime.
- **Reproducibility**: Backtests must output structured JSON via `scripts/run_backtest.py` containing key quantitative metrics:
  - Net Profit (%)
  - Win Rate (%)
  - Profit Factor
  - Max Drawdown (%)
  - Total Trades
  - Sharpe Ratio

## 2. Backtest Iteration Workflow (Agentic Optimization)
When testing indicator adjustments (e.g., adding ADX, RSI, or Volume filters):
1. Run `python scripts/run_backtest.py --strategy <StrategyName>`.
2. Inspect the JSON metrics output.
3. Compare against baseline strategy metrics.
4. **Keep changes** only if:
   - Net Profit or Expectancy improves, AND
   - Max Drawdown remains within safe threshold ($\le 15\%$).
5. **Revert changes** if metrics degrade.

## 3. Indian Market Specifics (NSE)
- Stock symbols follow NSE format (e.g., `RELIANCE.NS`, `TATAMOTORS.NS`, `HDFCBANK.NS`).
- Trading Hours: 9:15 AM to 3:30 PM IST.
- Daily candle evaluation is executed post-market or at 3:15 PM IST for swing entries.
