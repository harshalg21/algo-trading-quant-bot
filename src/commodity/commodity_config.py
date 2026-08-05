import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Distinct Low-Capital MCX Commodity Target Contracts (Mini & Micro)
MCX_COMMODITY_UNIVERSE = [
    {
        "symbol": "GC=F",
        "mcx_ticker": "GOLDPETAL",
        "name": "Gold Petal Futures (1 Gram)",
        "category": "PRECIOUS_METALS",
        "approx_margin_inr": 1328.25,   # Exact Upstox Margin for 1 Petal Lot
        "min_capital": 5000.0,
        "lot_size": 1
    },
    {
        "symbol": "GC=F",
        "mcx_ticker": "GOLDGUINEA",
        "name": "Gold Guinea Futures (8 Grams)",
        "category": "PRECIOUS_METALS",
        "approx_margin_inr": 6800.0,   # ~₹6,800 margin for 1 lot (Well within ₹20k)
        "min_capital": 10000.0,
        "lot_size": 1
    },
    {
        "symbol": "SI=F",
        "mcx_ticker": "SILVERMIC",
        "name": "Silver Micro Futures (1 Kg)",
        "category": "PRECIOUS_METALS",
        "approx_margin_inr": 9200.0,   # ~₹9,200 margin for 1 lot (Well within ₹20k)
        "min_capital": 10000.0,
        "lot_size": 1
    },
    {
        "symbol": "NG=F",
        "mcx_ticker": "NATGASMINI",
        "name": "Natural Gas Mini Futures",
        "category": "ENERGY",
        "approx_margin_inr": 12500.0,  # ~₹12,500 margin for 1 lot (Well within ₹20k)
        "min_capital": 15000.0,
        "lot_size": 1
    },
    {
        "symbol": "CL=F",
        "mcx_ticker": "CRUDEOILM",
        "name": "Crude Oil Mini Futures",
        "category": "ENERGY",
        "approx_margin_inr": 13800.0,  # ~₹13,800 margin for 1 lot (Well within ₹20k)
        "min_capital": 16000.0,
        "lot_size": 1
    }
]

# Commodity Capital & Risk Rules
COMMODITY_ACCOUNT_CAPITAL = 20000.0  # Tailored for ₹20,000 capital
MAX_COMMODITY_RISK_PCT = 1.5         # 1.5% Risk Cap per Commodity Trade (₹300 max risk)
TOP_COMMODITY_SIGNALS_LIMIT = 2      # Strict User Filter: Top 1-2 High Probability Signals Only
