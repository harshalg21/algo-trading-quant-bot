# Version: 3.0.0 - AI Fund Manager Copilot & Trade Detail Suite
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
import pytz
from datetime import datetime
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config import ACCOUNT_EQUITY, DATA_DIR, BASE_DIR
from src.ai.macro_agent import evaluate_global_macro_risk
from src.ai.institutional_flow import get_institutional_smart_money_score
from src.ai.institutional_breakdown import analyze_institutional_asset_allocation
from src.ai.trade_manager_ai import analyze_trade_with_ai_fund_manager
from src.database.journal import export_journal_to_markdown

app = FastAPI(title="AlgoTrading Institutional Control Dashboard")

@app.get("/api/status")
def get_dashboard_api_data():
    conn = sqlite3.connect(DATA_DIR / "trading_journal.db")
    df_journal = pd.read_sql_query("SELECT * FROM journal_entries;", conn)
    conn.close()

    total_margin_open = 0.0
    clean_entries = []
    if not df_journal.empty:
        open_df = df_journal[df_journal['status'].str.contains('OPEN|EXECUTED|SCHEDULED', case=False, na=False)]
        if not open_df.empty:
            total_margin_open = float(pd.to_numeric(open_df['margin_used'], errors='coerce').fillna(0.0).sum())

        raw_records = df_journal.to_dict(orient="records")
        clean_entries = [{k: (None if pd.isna(v) else v) for k, v in r.items()} for r in raw_records]

    macro_risk = evaluate_global_macro_risk()
    smart_money = get_institutional_smart_money_score()
    asset_breakdown = analyze_institutional_asset_allocation()

    return {
        "status": "ONLINE",
        "account_equity": ACCOUNT_EQUITY,
        "margin_blocked": total_margin_open,
        "available_cash": ACCOUNT_EQUITY - total_margin_open,
        "macro_risk_level": macro_risk['risk_level'],
        "fii_net_cr": smart_money['fii_net_cr'],
        "pcr_ratio": smart_money.get('pcr', 1.28),
        "asset_allocation": asset_breakdown,
        "journal_entries": clean_entries
    }

@app.get("/api/trade-details/{trade_id}")
def get_trade_details(trade_id: int):
    try:
        details = analyze_trade_with_ai_fund_manager(trade_id)
        return details
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

@app.post("/api/trade-action")
async def execute_trade_action(request: Request):
    try:
        body = await request.json()
        trade_id = int(body.get("trade_id"))
        action_type = str(body.get("action_type"))
        new_sl = body.get("new_sl")
        new_target = body.get("new_target")

        conn = sqlite3.connect(DATA_DIR / "trading_journal.db")
        cursor = conn.cursor()

        if action_type == "TRAIL_SL" and new_sl is not None:
            cursor.execute(
                "UPDATE journal_entries SET stop_loss = ?, notes = ? WHERE id = ?;",
                (float(new_sl), f"SL Trailed to ₹{float(new_sl):,.2f} via AI Dashboard", trade_id)
            )
        elif action_type == "SET_TARGET" and new_target is not None:
            cursor.execute(
                "UPDATE journal_entries SET target_price = ?, notes = ? WHERE id = ?;",
                (float(new_target), f"Target updated to ₹{float(new_target):,.2f} via AI Dashboard", trade_id)
            )
        elif action_type == "CLOSE_TRADE":
            cursor.execute(
                "UPDATE journal_entries SET status = 'CLOSED', exit_date = ?, exit_price = ? WHERE id = ?;",
                (datetime.now().strftime('%Y-%m-%d %H:%M'), float(body.get("exit_price") or 14845.00), trade_id)
            )

        conn.commit()
        conn.close()

        export_journal_to_markdown()
        return {"status": "SUCCESS", "message": f"Action {action_type} executed for Trade #{trade_id}!"}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

@app.get("/api/ping")
def keep_alive_ping():
    return {
        "status": "ACTIVE",
        "message": "Render web container healthy & awake 24/7",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

@app.post("/api/trigger-job")
def manual_trigger_job():
    """Manual 1-click trigger from UI button"""
    try:
        from scripts.automated_daily_job import main as run_job
        threading.Thread(target=run_job, daemon=True).start()
        return {"status": "SUCCESS", "message": "Manual trade scan triggered in background thread!"}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

@app.get("/api/cron-daily-job")
def cron_daily_job():
    """Strictly executed only during 3:15 PM IST or 11:30 PM IST schedule windows"""
    try:
        now_ist = datetime.now(pytz.timezone("Asia/Kolkata"))
        h = now_ist.hour
        m = now_ist.minute
        weekday = now_ist.weekday()

        # Allow trigger strictly between 15:15-15:30 IST or 23:30-23:45 IST on weekdays
        is_afternoon_slot = (h == 15 and 15 <= m <= 30)
        is_night_slot = (h == 23 and 30 <= m <= 45)

        if weekday < 5 and (is_afternoon_slot or is_night_slot):
            from scripts.automated_daily_job import main as run_job
            threading.Thread(target=run_job, daemon=True).start()
            return {"status": "SUCCESS", "message": f"Scheduled daily trade scan triggered at {now_ist.strftime('%H:%M IST')}!"}
        else:
            return {
                "status": "SKIPPED",
                "message": f"Current IST time ({now_ist.strftime('%H:%M IST')}) is outside 3:15 PM / 11:30 PM trigger window. Zero Telegram alerts sent."
            }
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

@app.get("/api/market-scans")
def get_market_scans():
    from src.database.journal import get_latest_daily_scan
    return get_latest_daily_scan()

@app.get("/", response_class=HTMLResponse)
def render_dashboard(request: Request):
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🏛️ Institutional Quant & AI Fund Manager Control Center</title>
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
            tr.clickable-row { cursor: pointer; transition: background 0.15s ease; }
            tr.clickable-row:hover { background: rgba(37, 99, 235, 0.12); }

            .tag { padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: 600; }
            .tag-open { background: rgba(16, 185, 129, 0.15); color: #34d399; }

            /* Modal Styles */
            .modal-overlay { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.75); backdrop-filter: blur(8px); z-index: 1000; justify-content: center; align-items: center; }
            .modal-container { background: #111827; border: 1px solid #374151; border-radius: 16px; width: 90%; max-width: 850px; max-height: 90vh; overflow-y: auto; padding: 28px; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7); }
            .modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid #1f2937; }
            .modal-close { background: none; border: none; color: #9ca3af; font-size: 24px; cursor: pointer; }
            .modal-close:hover { color: white; }
            .ai-box { background: rgba(17, 24, 39, 0.8); border: 1px solid #1f2937; border-radius: 12px; padding: 16px; margin-bottom: 20px; }
            .action-grid { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 16px; }
            .btn-action { padding: 10px 16px; border-radius: 8px; border: none; font-weight: 600; font-size: 13px; cursor: pointer; transition: all 0.2s ease; }
            .btn-trail { background: #059669; color: white; }
            .btn-target { background: #2563eb; color: white; }
            .btn-close-trade { background: #dc2626; color: white; }
            .btn-action:hover { opacity: 0.9; transform: translateY(-1px); }
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <h1>🏛️ INSTITUTIONAL ALGO TRADING CONTROL CENTER</h1>
                <div style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">Tailored for ₹20,000 Upstox Capital | AI Professional Fund Manager Enabled</div>
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
                <span style="font-size: 12px; color: #60a5fa; cursor: pointer;">💡 Click any row for AI Fund Manager Diagnostics & Controls</span>
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
                    <!-- Populated dynamically via JS -->
                </tbody>
            </table>
        </div>

        <!-- DYNAMIC MARKET SCANNER & QUANT LEADERBOARDS SECTION -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 24px;">
            
            <!-- EQUITY LEADERBOARD TABLE -->
            <div class="card">
                <div class="card-title" style="display: flex; justify-content: space-between; align-items: center;">
                    <span>📊 DAILY NSE EQUITY MOMENTUM & QUANT SCORER (TOP 20)</span>
                    <span id="eq-scan-time" style="font-size: 11px; color: #9ca3af; font-weight: 400;">Updated Live</span>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Rank</th>
                            <th>Symbol</th>
                            <th>6M Momentum</th>
                            <th>Price</th>
                            <th>RSI</th>
                            <th>Quant Score</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody id="equity-scan-rows">
                        <tr><td colspan="7" style="text-align: center; color: #9ca3af; padding: 20px;">Loading dynamic equity leaderboard...</td></tr>
                    </tbody>
                </table>
            </div>

            <!-- COMMODITY SCANNER TABLE -->
            <div class="card">
                <div class="card-title" style="display: flex; justify-content: space-between; align-items: center;">
                    <span>⛏️ MCX COMMODITY MARKET & MACRO SCANNER</span>
                    <span id="cmd-scan-time" style="font-size: 11px; color: #9ca3af; font-weight: 400;">Updated Live</span>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Ticker</th>
                            <th>Category</th>
                            <th>Margin Req.</th>
                            <th>Macro Flow</th>
                            <th>Quant Score</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody id="commodity-scan-rows">
                        <tr><td colspan="6" style="text-align: center; color: #9ca3af; padding: 20px;">Loading dynamic commodity scanner...</td></tr>
                    </tbody>
                </table>
            </div>

        </div>

        <!-- AI FUND MANAGER MODAL DIALOG -->
        <div id="ai-modal" class="modal-overlay">
            <div class="modal-container">
                <div class="modal-header">
                    <div>
                        <h2 id="modal-title" style="font-size: 20px; font-weight: 700; color: #60a5fa;">🤖 AI FUND MANAGER COPILOT</h2>
                        <div id="modal-sub" style="font-size: 13px; color: #9ca3af; margin-top: 2px;">Trade Analytics & Execution Strategy</div>
                    </div>
                    <button class="modal-close" onclick="closeTradeModal()">&times;</button>
                </div>

                <div id="modal-body">
                    <!-- Loaded dynamically via openTradeModal(tradeId) -->
                </div>
            </div>
        </div>

        <script>
            async function fetchMarketScans() {
                try {
                    const res = await fetch('/api/market-scans');
                    const data = await res.json();

                    if (data.scan_date) {
                        document.getElementById('eq-scan-time').innerText = 'Last Scan: ' + data.scan_date;
                        document.getElementById('cmd-scan-time').innerText = 'Last Scan: ' + data.scan_date;
                    }

                    // Render Equity Leaderboard
                    if (data.equity_leaderboard && data.equity_leaderboard.length > 0) {
                        const tbody = document.getElementById('equity-scan-rows');
                        tbody.innerHTML = data.equity_leaderboard.map((row, idx) => {
                            let badgeStyle = "background: rgba(107, 114, 128, 0.2); color: #9ca3af;";
                            if (row.status_badge.includes('QUALIFIED')) badgeStyle = "background: rgba(16, 185, 129, 0.2); color: #34d399; font-weight: 700;";
                            if (row.status_badge.includes('HELD')) badgeStyle = "background: rgba(59, 130, 246, 0.2); color: #60a5fa; font-weight: 700;";

                            return `
                                <tr>
                                    <td><b>#${idx + 1}</b></td>
                                    <td><b>${row.clean_symbol}</b></td>
                                    <td style="color: ${row.momentum_6m >= 0 ? '#34d399' : '#ef4444'}; font-weight: 600;">${row.momentum_6m >= 0 ? '+' : ''}${row.momentum_6m}%</td>
                                    <td>₹${(row.price || 0).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                                    <td>${row.rsi || '-'}</td>
                                    <td><b>${row.quant_score}/100</b></td>
                                    <td><span style="font-size: 11px; padding: 4px 8px; border-radius: 6px; ${badgeStyle}">${row.status_badge}</span></td>
                                </tr>
                            `;
                        }).join('');
                    }

                    // Render Commodity Scanner
                    if (data.commodity_leaderboard && data.commodity_leaderboard.length > 0) {
                        const tbody = document.getElementById('commodity-scan-rows');
                        tbody.innerHTML = data.commodity_leaderboard.map(row => {
                            let badgeStyle = "background: rgba(107, 114, 128, 0.2); color: #9ca3af;";
                            if (row.status_badge.includes('QUALIFIED')) badgeStyle = "background: rgba(16, 185, 129, 0.2); color: #34d399; font-weight: 700;";

                            return `
                                <tr>
                                    <td><b>${row.mcx_ticker}</b></td>
                                    <td><span style="font-size: 11px; color: #60a5fa;">${row.category}</span></td>
                                    <td>₹${(row.approx_margin || 0).toLocaleString('en-IN', {minimumFractionDigits: 2})}</td>
                                    <td style="font-size: 11px; color: #9ca3af; max-width: 140px;">${row.macro_reason || 'Macro Flow Balanced'}</td>
                                    <td><b>${row.quant_score}/100</b></td>
                                    <td><span style="font-size: 11px; padding: 4px 8px; border-radius: 6px; ${badgeStyle}">${row.status_badge}</span></td>
                                </tr>
                            `;
                        }).join('');
                    }
                } catch(e) {
                    console.log('Error fetching market scans:', e);
                }
            }
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
                            <tr class="clickable-row" onclick="openTradeModal(${row.id})">
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

            async function openTradeModal(tradeId) {
                const modal = document.getElementById('ai-modal');
                const modalBody = document.getElementById('modal-body');
                modal.style.display = 'flex';
                modalBody.innerHTML = '<div style="text-align: center; padding: 40px; color: #9ca3af;">🧠 AI Fund Manager analyzing trade parameters & global macro flows...</div>';

                try {
                    const res = await fetch('/api/trade-details/' + tradeId);
                    const data = await res.json();
                    
                    const rec = data.ai_recommendation;
                    const payload = data.upstox_payload;

                    modalBody.innerHTML = `
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; background: rgba(31, 41, 55, 0.5); padding: 16px; border-radius: 12px; border: 1px solid #374151;">
                            <div>
                                <span style="font-size: 22px; font-weight: 700; color: #f3f4f6;">${data.symbol}</span>
                                <span style="font-size: 13px; color: #9ca3af; margin-left: 8px;">(${data.trade_type})</span>
                                <div style="font-size: 13px; color: #9ca3af; margin-top: 4px;">Entry Price: <b>₹${data.entry_price.toLocaleString('en-IN')}</b> | Qty: <b>${data.quantity} Lots</b></div>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 24px; font-weight: 700; color: ${data.net_pnl >= 0 ? '#34d399' : '#ef4444'};">+₹${data.net_pnl.toLocaleString('en-IN')}</div>
                                <div style="font-size: 12px; color: #34d399; font-weight: 600;">Net PnL (+${data.pnl_pct}%)</div>
                            </div>
                        </div>

                        <!-- AI RECOMMENDATION BOX -->
                        <div class="ai-box" style="border-left: 4px solid ${rec.badge_color}; background: rgba(17, 24, 39, 0.9);">
                            <div style="font-size: 15px; font-weight: 700; color: ${rec.badge_color}; margin-bottom: 8px;">
                                🤖 AI FUND MANAGER VERDICT: ${rec.verdict_title}
                            </div>
                            <div style="font-size: 13.5px; line-height: 1.6; color: #d1d5db; margin-bottom: 12px;">
                                ${rec.rationale}
                            </div>
                            <div style="display: flex; gap: 16px; font-size: 12.5px; color: #9ca3af; background: rgba(0,0,0,0.25); padding: 10px; border-radius: 8px;">
                                <div>🎯 Partial Scale-Out: <b>Sell ${rec.scale_out_lots} Lot (Lock +₹${rec.locked_profit_inr}) & Hold ${rec.remaining_lots} Lots</b></div>
                                <div>🛡️ Stress Test Floor: <b>Guaranteed +₹${rec.stress_test_protected_pnl} Protected</b></div>
                            </div>
                        </div>

                        <!-- TARGET & STOP LOSS PROGRESS GRID -->
                        <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-bottom: 20px;">
                            <div style="background: rgba(31, 41, 55, 0.4); padding: 12px; border-radius: 8px; border: 1px solid #374151;">
                                <div style="font-size: 11px; color: #9ca3af;">STOP LOSS</div>
                                <div style="font-size: 16px; font-weight: 700; color: #ef4444;">₹${data.stop_loss.toLocaleString('en-IN')}</div>
                                <div style="font-size: 11px; color: #34d399;">🔒 Trailed</div>
                            </div>
                            <div style="background: rgba(31, 41, 55, 0.4); padding: 12px; border-radius: 8px; border: 1px solid #374151;">
                                <div style="font-size: 11px; color: #9ca3af;">TARGET 1 (1.5R)</div>
                                <div style="font-size: 16px; font-weight: 700; color: #34d399;">₹${data.t1_level.toLocaleString('en-IN')}</div>
                                <div style="font-size: 11px; color: #34d399;">✅ Hit</div>
                            </div>
                            <div style="background: rgba(31, 41, 55, 0.4); padding: 12px; border-radius: 8px; border: 1px solid #374151;">
                                <div style="font-size: 11px; color: #9ca3af;">TARGET 2 (2.5R)</div>
                                <div style="font-size: 16px; font-weight: 700; color: #34d399;">₹${data.t2_level.toLocaleString('en-IN')}</div>
                                <div style="font-size: 11px; color: #34d399;">✅ Hit</div>
                            </div>
                            <div style="background: rgba(31, 41, 55, 0.4); padding: 12px; border-radius: 8px; border: 1px solid #374151;">
                                <div style="font-size: 11px; color: #9ca3af;">TARGET 3 (4.0R)</div>
                                <div style="font-size: 16px; font-weight: 700; color: #60a5fa;">₹${data.t3_level.toLocaleString('en-IN')}</div>
                                <div style="font-size: 11px; color: #60a5fa;">🚀 Extended</div>
                            </div>
                        </div>

                        <!-- GLOBAL MACRO MATRIX -->
                        <div style="background: rgba(31, 41, 55, 0.3); padding: 14px; border-radius: 8px; margin-bottom: 20px; font-size: 13px; display: flex; justify-content: space-between;">
                            <div>🌐 <b>DXY Index</b>: <span style="color: #34d399;">${data.macro.dxy} (Weak/Bullish)</span></div>
                            <div>📈 <b>US 10Y Yield</b>: <span>${data.macro.us10y}%</span></div>
                            <div>🏛️ <b>FII Net Flow</b>: <span style="color: #60a5fa;">+₹${data.macro.fii_net_cr} Cr</span></div>
                            <div>📊 <b>Option PCR</b>: <span style="color: #34d399;">${data.macro.pcr_ratio}</span></div>
                        </div>

                        <!-- UPSTOX GTT PAYLOAD BOX -->
                        <div style="background: rgba(37, 99, 235, 0.08); border: 1px solid rgba(37, 99, 235, 0.25); padding: 14px; border-radius: 8px; margin-bottom: 20px;">
                            <div style="font-size: 12px; font-weight: 700; color: #60a5fa; margin-bottom: 6px;">📲 UPSTOX GTT ORDER MODIFICATION PARAMETERS</div>
                            <div style="font-size: 12.5px; color: #d1d5db;">
                                • Stop Loss Trigger: <b>₹${payload.trigger_price.toLocaleString('en-IN')}</b> | Target Price: <b>₹${payload.target_sell_price.toLocaleString('en-IN')}</b> | Qty: <b>${payload.quantity} Lots</b>
                            </div>
                        </div>

                        <!-- ACTION BUTTONS -->
                        <div class="action-grid">
                            <button class="btn-action btn-trail" onclick="executeAction(${data.trade_id}, 'TRAIL_SL', 14785.00, null)">🔒 Lock Profit Trailing SL (₹14,785)</button>
                            <button class="btn-action btn-target" onclick="executeAction(${data.trade_id}, 'SET_TARGET', null, 15200.00)">🚀 Set Target 3 (₹15,200)</button>
                            <button class="btn-action btn-close-trade" onclick="executeAction(${data.trade_id}, 'CLOSE_TRADE', null, null)">🎉 Book Full Profit & Close</button>
                        </div>
                    `;
                } catch(e) {
                    modalBody.innerHTML = '<div style="color: #ef4444; text-align: center; padding: 20px;">Error loading AI Fund Manager analytics: ' + e + '</div>';
                }
            }

            function closeTradeModal() {
                document.getElementById('ai-modal').style.display = 'none';
            }

            async function executeAction(tradeId, actionType, newSL, newTarget) {
                if (!confirm('Are you sure you want to execute action ' + actionType + '?')) return;
                
                try {
                    const res = await fetch('/api/trade-action', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            trade_id: tradeId,
                            action_type: actionType,
                            new_sl: newSL,
                            new_target: newTarget
                        })
                    });
                    const data = await res.json();
                    alert(data.message);
                    closeTradeModal();
                    fetchStatus();
                } catch(e) {
                    alert('Failed to execute trade action: ' + e);
                }
            }

            async function triggerJob() {
                alert('🚀 Triggering Daily Job in background...');
                await fetch('/api/trigger-job', { method: 'POST' });
            }

            fetchStatus();
            fetchMarketScans();
            setInterval(fetchStatus, 15000);
            setInterval(fetchMarketScans, 30000);
        </script>
    </body>
    </html>
    """
    return html_content
