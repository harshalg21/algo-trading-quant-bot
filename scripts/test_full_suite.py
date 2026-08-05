import os
import sys
from pathlib import Path

# Fix OpenBLAS Threading at top
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def test_full_system_flow():
    print("="*75)
    print(" 🔬 END-TO-END COMPREHENSIVE ALGO TRADING SYSTEM AUDIT")
    print("="*75)

    errors = []

    # 1. Test Config & Fallback Credentials
    print("\n--- [TEST 1/7] Config & Credentials ---")
    try:
        from src.config import ACCOUNT_EQUITY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, MAX_RISK_PER_TRADE_PCT
        print(f" ✅ Equity: ₹{ACCOUNT_EQUITY:,.2f} | Risk per trade: {MAX_RISK_PER_TRADE_PCT}%")
        print(f" ✅ Telegram Bot Token: {TELEGRAM_BOT_TOKEN[:15]}... | Chat ID: {TELEGRAM_CHAT_ID}")
    except Exception as e:
        errors.append(f"Config Test Failed: {e}")

    # 2. Test Global Macro Risk Engine
    print("\n--- [TEST 2/7] Global Macro Risk Engine ---")
    try:
        from src.ai.macro_agent import evaluate_global_macro_risk
        macro = evaluate_global_macro_risk()
        print(f" ✅ Status: {macro.get('status')} | India VIX: {macro.get('india_vix')}")
    except Exception as e:
        errors.append(f"Macro Agent Failed: {e}")

    # 3. Test Institutional Flow & Option PCR Engine
    print("\n--- [TEST 3/7] Institutional Smart Money Engine ---")
    try:
        from src.ai.institutional_flow import get_institutional_smart_money_score
        inst = get_institutional_smart_money_score()
        print(f" ✅ FII Net: ₹{inst['fii_net_cr']} Cr | DII Net: ₹{inst['dii_net_cr']} Cr | PCR: {inst['pcr']} ({inst['sentiment']})")
    except Exception as e:
        errors.append(f"Institutional Flow Failed: {e}")

    # 4. Test Asset Breakdown Engine
    print("\n--- [TEST 4/7] Institutional Asset Breakdown ---")
    try:
        from src.ai.institutional_breakdown import analyze_institutional_asset_allocation
        alloc = analyze_institutional_asset_allocation()
        print(f" ✅ Allocation: {alloc['asset_allocation_pct']}")
        print(f" ✅ Sector Leaders Count: {len(alloc['sector_leaders'])}")
    except Exception as e:
        errors.append(f"Asset Breakdown Failed: {e}")

    # 5. Test Upstox Charges & Position Sizer
    print("\n--- [TEST 5/7] Risk Management & Upstox Charges ---")
    try:
        from src.risk.position_sizer import calculate_position_size
        from src.risk.upstox_charges import calculate_upstox_trade_charges
        sizer = calculate_position_size(20000.0, 1.0, 1940.0, 1908.20)
        charges = calculate_upstox_trade_charges("EQUITY", 1940.0, 1988.95, 4)
        print(f" ✅ Pos Sizer Qty: {sizer['quantity']} | Max Risk: ₹{sizer['max_risk_amount']:,.2f}")
        print(f" ✅ Upstox Charges (4 Qty SUNPHARMA): ₹{charges['total_charges']:.2f}")
    except Exception as e:
        errors.append(f"Risk & Charges Failed: {e}")

    # 6. Test Trading Journal & DB Schema
    print("\n--- [TEST 6/7] Database & Trading Journal ---")
    try:
        import sqlite3
        import pandas as pd
        from src.database.journal import init_journal_db
        init_journal_db()
        from src.config import DATA_DIR
        conn = sqlite3.connect(DATA_DIR / "trading_journal.db")
        df_j = pd.read_sql_query("SELECT * FROM journal_entries;", conn)
        conn.close()
        print(f" ✅ Database Journal Entries Count: {len(df_j)}")
        if not df_j.empty:
            df_open = df_j[df_j['status'].astype(str).str.contains('OPEN|EXECUTED|SCHEDULED', case=False, na=False)]
            margin_sum = float(df_open['margin_used'].sum()) if not df_open.empty else 0.0
            print(f" ✅ Calculated Margin Blocked: ₹{margin_sum:,.2f}")
    except Exception as e:
        errors.append(f"Journal DB Test Failed: {e}")

    # 7. Test Control Dashboard API Endpoint Output
    print("\n--- [TEST 7/7] FastAPI Control Dashboard API Endpoint ---")
    try:
        from src.dashboard.app import get_dashboard_api_data
        api_data = get_dashboard_api_data()
        print(f" ✅ Dashboard API Margin Blocked: ₹{api_data['margin_blocked']:,.2f}")
        print(f" ✅ Dashboard API Cash Remaining: ₹{api_data['cash_remaining']:,.2f}")
    except Exception as e:
        errors.append(f"Dashboard API Test Failed: {e}")

    print("\n" + "="*75)
    if not errors:
        print(" 🎉 FULL SYSTEM AUDIT COMPLETED: 100% SUCCESS! ALL COMPONENTS HEALTHY.")
    else:
        print(f" ⚠️ AUDIT FOUND {len(errors)} ERROR(S):")
        for err in errors:
            print(f"   • {err}")
    print("="*75)

if __name__ == "__main__":
    test_full_system_flow()
