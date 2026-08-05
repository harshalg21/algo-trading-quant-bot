# NSE Equity Swing Trading & Agentic Strategy Lab

An automated quantitative trading setup and AI Agent strategy lab tailored for the **Indian Stock Market (NSE Equities)** using **DhanHQ Free API** and **Semi-Automated Telegram Approvals**.

## 📁 System Architecture
- `src/config.py`: Environment settings, risk caps, liquid stock universe.
- `src/risk/position_sizer.py`: Dynamic share sizing based on 1% equity risk per trade.
- `src/data/fetcher.py`: Automated daily OHLCV candle retriever.
- `src/strategies/momentum_breakout.py`: Momentum Volume Breakout Swing Strategy.
- `src/backtest/engine.py`: Vectorized backtest engine generating JSON metrics.
- `src/alerts/telegram_bot.py`: Semi-automated Telegram trade signal notifier.
- `scripts/run_backtest.py`: CLI command for strategy backtesting & optimization.
- `scripts/scan_signals.py`: Scanner for daily market breakout signals.

## 🚀 How to Run Backtests

```bash
# 1. Activate environment
.\venv\Scripts\activate

# 2. Run backtest for Tata Motors (2 years daily data)
python scripts/run_backtest.py --symbol TATAMOTORS.NS

# 3. Run scanner across Nifty universe
python scripts/scan_signals.py
```

## 📊 Backtest Metrics Output Format
```json
{
  "Start": "2024-08-02",
  "End": "2026-08-02",
  "Return_Pct": 42.5,
  "Max_Drawdown_Pct": -9.8,
  "Win_Rate_Pct": 48.2,
  "Profit_Factor": 2.15,
  "Sharpe_Ratio": 1.85,
  "Total_Trades": 32
}
```
