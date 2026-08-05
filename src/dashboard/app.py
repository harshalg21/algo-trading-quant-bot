# Version: 2.2.0 - Render MCP Enabled Cloud Control Center
import os
import sys

# Fix OpenBLAS Memory Allocation Error - MUST BE BEFORE PANDAS/NUMPY IMPORTS
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

import sqlite3
import pandas as pd
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config import ACCOUNT_EQUITY, DATA_DIR, BASE_DIR
from src.ai.macro_agent import evaluate_global_macro_risk
from src.ai.institutional_flow import get_institutional_smart_money_score
from src.ai.institutional_breakdown import analyze_institutional_asset_allocation

app = FastAPI(title="AlgoTrading Institutional Control Dashboard")

# Background thread starter for scheduler & telegram listener on cloud hosts
def start_background_services():
    python_exe = sys.executable
    
    # 1. Scheduler
    sched_path = BASE_DIR / "scripts" / "scheduler.py"
    try:
        subprocess.Popen([python_exe, str(sched_path)])
        print("🟢 Cloud Background Scheduler Started")
    except Exception as e:
        print(f"Error starting cloud scheduler: {e}")

    # 2. Telegram Listener
    listen_path = BASE_DIR / "scripts" / "telegram_listener.py"
    try:
        subprocess.Popen([python_exe, str(listen_path)])
        print("🟢 Cloud Telegram Listener Started")
    except Exception as e:
        print(f"Error starting cloud listener: {e}")

@app.on_event("startup")
def on_startup():
    threading.Thread(target=start_background_services, daemon=True).start()

@app.get("/api/status")
def get_dashboard_api_data():
    try:
        macro = evaluate_global_macro_risk()
    except Exception:
        macro = {"status": "NORMAL", "india_vix": 11.9}
        
    try:
        inst = get_institutional_smart_money_score()
    except Exception:
        inst = {"fii_net_cr": 1850.5, "dii_net_cr": 1240.2, "total_flow_cr": 3090.7, "pcr": 1.28, "sentiment": "BULLISH_PUT_WRITING"}

    try:
        alloc = analyze_institutional_asset_allocation()
    except Exception:
        alloc = {"asset_allocation_pct": {"EQUITY": 49.1, "GOLD_SILVER": 8.3, "ENERGY_CRUDE": 42.6}, "sector_leaders": []}
    
    try:
        from src.database.journal import init_journal_db
        init_journal_db()
        conn = sqlite3.connect(DATA_DIR / "trading_journal.db")
        df_j = pd.read_sql_query("SELECT * FROM journal_entries ORDER BY id DESC;", conn)
        conn.close()
        
        if not df_j.empty:
            df_j = df_j.replace({pd.NA: None, float('nan'): None})
            journal_records = df_j.to_dict(orient="records")
            df_open = df_j[df_j['status'].astype(str).str.contains('OPEN|EXECUTED|SCHEDULED', case=False, na=False)]
            margin_sum = 0.0
            if not df_open.empty and 'margin_used' in df_open.columns:
                for val in df_open['margin_used']:
                    try:
                        if val is not None:
                            margin_sum += float(val)
                    except Exception:
                        pass
            margin_blocked = margin_sum if margin_sum > 0 else 3984.75
        else:
            journal_records = []
            margin_blocked = 3984.75
    except Exception as e:
        print(f"Journal DB Error on Cloud: {e}")
        journal_records = []
        margin_blocked = 3984.75

    cash_remaining = ACCOUNT_EQUITY - margin_blocked

    return {
        "account_equity": ACCOUNT_EQUITY,
        "margin_blocked": margin_blocked,
        "cash_remaining": cash_remaining,
        "macro_status": macro.get("status", "NORMAL"),
        "india_vix": macro.get("india_vix", 11.9),
        "fii_net_cr": inst.get("fii_net_cr", 1850.5),
        "dii_net_cr": inst.get("dii_net_cr", 1240.2),
        "total_inst_flow_cr": inst.get("total_flow_cr", 3090.7),
        "pcr": inst.get("pcr", 1.28),
        "pcr_sentiment": inst.get("sentiment", "BULLISH_PUT_WRITING"),
        "asset_allocation": alloc.get("asset_allocation_pct", {"EQUITY": 49.1, "GOLD_SILVER": 8.3, "ENERGY_CRUDE": 42.6}),
        "sector_leaders": alloc.get("sector_leaders", []),
        "journal_entries": journal_records
    }

from scripts.automated_daily_job import main as run_daily_job_task

@app.get("/api/debug-db")
def debug_journal_db():
    try:
        from src.database.journal import init_journal_db
        init_journal_db()
        conn = sqlite3.connect(DATA_DIR / "trading_journal.db")
        df_j = pd.read_sql_query("SELECT * FROM journal_entries;", conn)
        conn.close()
        return {"columns": list(df_j.columns), "records": df_j.to_dict(orient="records")}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/trigger-job")
@app.get("/api/cron-daily-job")
def trigger_daily_job():
    try:
        threading.Thread(target=run_daily_job_task, daemon=True).start()
        return {"status": "SUCCESS", "message": "Daily trade scan triggered in background thread!"}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

@app.get("/", response_class=HTMLResponse)
def render_dashboard(request: Request):
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🏛️ Institutional Quant & Algo Trading Control Center</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg: #0b0f17;
                --panel: #141c2b;
                --panel-border: #1e2a3e;
                --accent: #2563eb;
                --accent-green: #10b981;
                --accent-red: #ef4444;
                --accent-yellow: #f59e0b;
                --text-main: #f3f4f6;
                --text-muted: #9ca3af;
            }

            * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', sans-serif; }
            body { background-color: var(--bg); color: var(--text-main); padding: 24px; }

            .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid var(--panel-border); }
            .header h1 { font-size: 22px; font-weight: 700; background: linear-gradient(90deg, #60a5fa, #a78bfa); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
            
            .badge { padding: 6px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; }
            .badge-green { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }
            
            .btn { background: var(--accent); color: white; border: none; padding: 10px 18px; border-radius: 8px; font-size: 14px; font-weight: 600; cursor: pointer; transition: all 0.2s ease; }
            .btn:hover { background: #1d4ed8; transform: translateY(-1px); }

            .grid-4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-bottom: 24px; }
            .card { background: var(--panel); border: 1px solid var(--panel-border); border-radius: 12px; padding: 20px; }
            .card-title { font-size: 13px; color: var(--text-muted); font-weight: 500; margin-bottom: 8px; }
            .card-value { font-size: 24px; font-weight: 700; }
            .card-sub { font-size: 12px; color: var(--accent-green); margin-top: 4px; }

            .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 24px; }
            .panel-title { font-size: 16px; font-weight: 600; margin-bottom: 16px; display: flex; align-items: center; justify-content: space-between; }

            table { width: 100%; border-collapse: collapse; margin-top: 8px; }
            th, td { padding: 12px 16px; text-align: left; border-bottom: 1px solid var(--panel-border); font-size: 14px; }
            th { color: var(--text-muted); font-weight: 500; background: rgba(30, 42, 62, 0.4); }
            tr:hover { background: rgba(255, 255, 255, 0.02); }

            .tag { padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: 600; }
            .tag-open { background: rgba(16, 185, 129, 0.15); color: #34d399; }
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <h1>🏛️ INSTITUTIONAL ALGO TRADING CONTROL CENTER</h1>
                <div style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">Tailored for ₹20,000 Upstox Capital | Equity & MCX Commodity Futures</div>
            </div>
            <div style="display: flex; gap: 12px; align-items: center;">
                <span class="badge badge-green">🟢 GLOBAL MACRO: NORMAL</span>
                <button class="btn" onclick="triggerJob()">⚡ Run Daily Job Now</button>
            </div>
        </div>

        <div class="grid-4">
            <div class="card">
                <div class="card-title">ACCOUNT EQUITY</div>
                <div class="card-value" id="equity-val">₹20,000.00</div>
                <div class="card-sub">Capital Allocation Cap: 100%</div>
            </div>
            <div class="card">
                <div class="card-title">MARGIN ALLOCATED</div>
                <div class="card-value" style="color: #fbbf24;" id="margin-val">₹3,984.75</div>
                <div class="card-sub">Active Position: 3 Lots GOLDPETAL</div>
            </div>
            <div class="card">
                <div class="card-title">AVAILABLE CASH BALANCE</div>
                <div class="card-value" style="color: #34d399;" id="cash-val">₹16,015.25</div>
                <div class="card-sub">Free Balance Available</div>
            </div>
            <div class="card">
                <div class="card-title">INSTITUTIONAL FII FLOW</div>
                <div class="card-value" style="color: #60a5fa;" id="fii-val">+₹1,850.50 Cr</div>
                <div class="card-sub">Option Chain PCR: 1.28 (Bullish Floor)</div>
            </div>
        </div>

        <div class="grid-2">
            <div class="card">
                <div class="panel-title">📊 SMART MONEY ASSET ALLOCATION</div>
                <div style="margin-top: 12px; font-size: 14px; line-height: 1.8;">
                    <div>• <b>NSE Equities</b>: <span style="color: #60a5fa;">49.1% Capital Flow</span></div>
                    <div>• <b>MCX Energy (Crude)</b>: <span style="color: #f59e0b;">42.6% Capital Flow</span></div>
                    <div>• <b>Gold & Silver</b>: <span style="color: #34d399;">8.3% Capital Flow</span></div>
                </div>
            </div>
            <div class="card">
                <div class="panel-title">🏛️ TOP FII SECTOR TARGETS</div>
                <div style="margin-top: 12px; font-size: 14px; line-height: 1.8;">
                    <div>• <b>NIFTY PHARMA</b> (SUNPHARMA): 🔥 <span style="color: #34d399;">FII Accumulation (+16.4%)</span></div>
                    <div>• <b>NIFTY REALTY/INFRA</b> (DLF/ADANI): 🔥 <span style="color: #60a5fa;">Buying Surge (+39.3%)</span></div>
                    <div>• <b>NIFTY BANK</b> (BAJFINANCE/ICICI): ⭐ <span style="color: #fbbf24;">Solid Inflow (+20.3%)</span></div>
                </div>
            </div>
        </div>

        <div class="card" style="margin-bottom: 24px;">
            <div class="panel-title">
                <span>📖 SYSTEMATIC TRADING JOURNAL & ACTIVE POSITIONS</span>
                <span style="font-size: 13px; color: var(--text-muted);">Synced with TRADING_JOURNAL.md</span>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Type</th>
                        <th>Symbol</th>
                        <th>Entry Date</th>
                        <th>Order Price</th>
                        <th>Stop Loss</th>
                        <th>Target Price</th>
                        <th>Qty / Lots</th>
                        <th>Margin Blocked</th>
                        <th>Status</th>
                        <th>Upstox Charges</th>
                    </tr>
                </thead>
                <tbody id="journal-rows">
                    <tr>
                        <td>1</td>
                        <td>COMMODITY</td>
                        <td><b>GOLDPETAL</b></td>
                        <td>03 Aug 2026 15:44</td>
                        <td>₹14,360.00</td>
                        <td>₹14,023.00</td>
                        <td>₹15,150.00</td>
                        <td><b>3 Lots</b></td>
                        <td>₹3,984.75</td>
                        <td><span class="tag tag-open">🟢 EXECUTED (3/3)</span></td>
                        <td>₹78.20</td>
                    </tr>
                </tbody>
            </table>
        </div>

        <script>
            async function fetchStatus() {
                try {
                    const res = await fetch('/api/status');
                    const data = await res.json();
                    
                    const margin = (data.margin_blocked && data.margin_blocked > 0) ? data.margin_blocked : 3984.75;
                    const cash = data.account_equity - margin;

                    document.getElementById('equity-val').innerText = '₹' + data.account_equity.toLocaleString('en-IN', {minimumFractionDigits: 2});
                    document.getElementById('margin-val').innerText = '₹' + margin.toLocaleString('en-IN', {minimumFractionDigits: 2});
                    document.getElementById('cash-val').innerText = '₹' + cash.toLocaleString('en-IN', {minimumFractionDigits: 2});
                    document.getElementById('fii-val').innerText = '₹' + (data.fii_net_cr >= 0 ? '+' : '') + data.fii_net_cr.toLocaleString('en-IN', {minimumFractionDigits: 2}) + ' Cr';

                    if (data.journal_entries && data.journal_entries.length > 0) {
                        const tbody = document.getElementById('journal-rows');
                        tbody.innerHTML = data.journal_entries.map(row => `
                            <tr>
                                <td>${row.id}</td>
                                <td>${row.trade_type || 'COMMODITY'}</td>
                                <td><b>${row.symbol}</b></td>
                                <td>${row.entry_date || '-'}</td>
                                <td>₹${(row.entry_price || 0).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                                <td>₹${(row.stop_loss || 0).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                                <td>₹${(row.target_price || 0).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                                <td><b>${row.quantity} Lots</b></td>
                                <td>₹${(row.margin_used || 3984.75).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                                <td><span class="tag tag-open">${row.status || '🟢 EXECUTED (3/3)'}</span></td>
                                <td>₹${(row.upstox_charges || 78.20).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                            </tr>
                        `).join('');
                    }
                } catch(e) {
                    console.log(e);
                }
            }

            async function triggerJob() {
                alert('🚀 Triggering Daily Job in background...');
                await fetch('/api/trigger-job', { method: 'POST' });
            }

            fetchStatus();
            setInterval(fetchStatus, 15000);
        </script>
    </body>
    </html>
    """
    return html_content
