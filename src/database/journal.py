import sqlite3
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

# Force UTF-8 for console output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config import ACCOUNT_EQUITY, TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, BASE_DIR, DATA_DIR
from src.risk.upstox_charges import calculate_upstox_trade_charges

JOURNAL_DB_PATH = DATA_DIR / "trading_journal.db"
JOURNAL_MD_PATH = BASE_DIR / "TRADING_JOURNAL.md"

def init_journal_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(JOURNAL_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_type TEXT,
            symbol TEXT,
            entry_date TEXT,
            entry_price REAL,
            stop_loss REAL,
            target_price REAL,
            quantity INTEGER,
            margin_used REAL,
            status TEXT,
            exit_date TEXT,
            exit_price REAL,
            upstox_charges REAL,
            gross_pnl REAL,
            net_pnl REAL,
            pnl_pct REAL,
            holding_days INTEGER,
            notes TEXT
        );
    """)
    try:
        cursor.execute("ALTER TABLE journal_entries ADD COLUMN pnl_pct REAL;")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE journal_entries ADD COLUMN holding_days INTEGER;")
    except Exception:
        pass
    cursor.execute("SELECT COUNT(*) FROM journal_entries;")
    count = cursor.fetchone()[0]
    if count == 0:
        try:
            charges = calculate_upstox_trade_charges("COMMODITY", 14360.0, 0.0, 3)
            chg_val = charges['total_charges']
        except Exception:
            chg_val = 78.20
        cursor.execute("""
            INSERT INTO journal_entries (trade_type, symbol, entry_date, entry_price, stop_loss, target_price, quantity, margin_used, status, upstox_charges, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, ("COMMODITY", "GOLDPETAL", "2026-08-03 15:44", 14360.0, 14023.0, 15150.0, 3, 3984.75, "🟢 EXECUTED (3/3)", chg_val, "Live Active MCX Position"))
    
    conn.commit()
    conn.close()

def log_trade_to_journal(
    trade_type: str,
    symbol: str,
    entry_price: float,
    stop_loss: float,
    target_price: float,
    quantity: int,
    margin_used: float = 0.0,
    status: str = "SCHEDULED",
    notes: str = "GTT Order Placed on Upstox"
):
    init_journal_db()
    conn = sqlite3.connect(JOURNAL_DB_PATH)
    cursor = conn.cursor()
    today_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    charges = calculate_upstox_trade_charges(trade_type, entry_price, 0.0, quantity)
    
    # Check if entry exists
    cursor.execute("SELECT id FROM journal_entries WHERE symbol = ? AND status IN ('SCHEDULED', 'OPEN', 'EXECUTED')", (symbol,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE journal_entries
            SET quantity = ?, margin_used = ?, status = ?, notes = ?
            WHERE id = ?;
        """, (quantity, margin_used, status, notes, existing[0]))
    else:
        cursor.execute("""
            INSERT INTO journal_entries (trade_type, symbol, entry_date, entry_price, stop_loss, target_price, quantity, margin_used, status, upstox_charges, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (trade_type, symbol, today_str, entry_price, stop_loss, target_price, quantity, margin_used, status, charges['total_charges'], notes))
    
    conn.commit()
    conn.close()
    
    export_journal_to_markdown()

def close_trade_in_journal(symbol: str, exit_price: float, notes: str = "Trade Closed"):
    init_journal_db()
    conn = sqlite3.connect(JOURNAL_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, trade_type, entry_date, entry_price, quantity, margin_used FROM journal_entries WHERE symbol = ? AND status IN ('OPEN', 'EXECUTED')", (symbol,))
    trade = cursor.fetchone()
    
    if trade:
        trade_id, trade_type, entry_date_str, entry_p, qty, margin = trade
        exit_date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Calculate Holding Days
        try:
            d_entry = datetime.strptime(entry_date_str, "%Y-%m-%d %H:%M")
            d_exit = datetime.now()
            holding_days = max(1, (d_exit - d_entry).days)
        except Exception:
            holding_days = 1

        charges = calculate_upstox_trade_charges(trade_type, entry_p, exit_price, qty)
        tot_charges = charges['total_charges']
        
        capital_base = margin if margin > 0 else (entry_p * qty)
        gross_pnl = (exit_price - entry_p) * qty
        net_pnl = gross_pnl - tot_charges
        pnl_pct = (net_pnl / capital_base) * 100.0 if capital_base > 0 else 0.0
        
        cursor.execute("""
            UPDATE journal_entries
            SET status = 'CLOSED', exit_date = ?, exit_price = ?, upstox_charges = ?, gross_pnl = ?, net_pnl = ?, pnl_pct = ?, holding_days = ?, notes = ?
            WHERE id = ?;
        """, (exit_date_str, exit_price, tot_charges, gross_pnl, net_pnl, pnl_pct, holding_days, notes, trade_id))
        
        conn.commit()
    conn.close()
    
    export_journal_to_markdown()

def export_journal_to_markdown():
    init_journal_db()
    conn = sqlite3.connect(JOURNAL_DB_PATH)
    df = pd.read_sql_query("SELECT * FROM journal_entries ORDER BY id DESC;", conn)
    conn.close()

    md_content = f"# 📖 SYSTEMATIC TRADING JOURNAL & PERFORMANCE LOG\n\n"
    md_content += f"*Last Updated: {datetime.now().strftime('%d %b %Y %H:%M')}*\n\n"

    if df.empty:
        md_content += "_No trades logged in journal yet. Execute a trade and tap button to log!_\n"
    else:
        md_content += "| ID | Type | Symbol | Entry Date | Exit Date | Holding Duration | Entry Price | Target | Stop Loss | Qty/Lots | Margin Blocked | Status | Exit Price | Upstox Charges | Net PnL (₹) | Net PnL (%) |\n"
        md_content += "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n"
        
        for _, r in df.iterrows():
            entry_d = str(r['entry_date']) if r['entry_date'] else "-"
            exit_d = str(r['exit_date']) if r['exit_date'] else "-"
            
            # Holding Duration logic
            st = str(r['status']).upper()
            if st == "CLOSED":
                duration_str = f"{r['holding_days']} Days" if r['holding_days'] else "1 Day"
            else:
                try:
                    d_ent = datetime.strptime(entry_d, "%Y-%m-%d %H:%M")
                    days_active = max(1, (datetime.now() - d_ent).days)
                    duration_str = f"{days_active} Days (Active)"
                except Exception:
                    duration_str = "Active Holding"

            net_pnl_str = f"₹{r['net_pnl']:+,.2f}" if r['net_pnl'] is not None else "-"
            pnl_pct_str = f"{r['pnl_pct']:+,.2f}%" if r['pnl_pct'] is not None else "-"
            exit_p_str = f"₹{r['exit_price']:,.2f}" if r['exit_price'] is not None else "-"
            charges_str = f"₹{r['upstox_charges']:,.2f}" if r['upstox_charges'] is not None else "₹0.00"
            
            if st == "SCHEDULED":
                status_badge = f"⏳ GTT SCHEDULED (0/{r['quantity']})"
            elif st in ["OPEN", "EXECUTED"]:
                status_badge = f"🟢 EXECUTED ({r['quantity']}/{r['quantity']})"
            elif st == "CLOSED":
                status_badge = "🎉 WIN" if r['net_pnl'] and r['net_pnl'] > 0 else "🛑 LOSS"
            else:
                status_badge = st

            md_content += (
                f"| {r['id']} | {r['trade_type']} | **{r['symbol']}** | {entry_d} | {exit_d} | "
                f"**{duration_str}** | ₹{r['entry_price']:,.2f} | ₹{r['target_price']:,.2f} | ₹{r['stop_loss']:,.2f} | "
                f"**{r['quantity']} Lots** | ₹{r['margin_used']:,.2f} | {status_badge} | {exit_p_str} | {charges_str} | **{net_pnl_str}** | **{pnl_pct_str}** |\n"
            )

    with open(JOURNAL_MD_PATH, "w", encoding="utf-8") as f:
        f.write(md_content)

def send_eod_telegram_journal_summary():
    init_journal_db()
    conn = sqlite3.connect(JOURNAL_DB_PATH)
    df_sched = pd.read_sql_query("SELECT * FROM journal_entries WHERE status LIKE '%SCHEDULED%';", conn)
    df_open = pd.read_sql_query("SELECT * FROM journal_entries WHERE status LIKE '%OPEN%' OR status LIKE '%EXECUTED%';", conn)
    df_closed = pd.read_sql_query("SELECT * FROM journal_entries WHERE status LIKE '%CLOSED%' OR status LIKE '%WIN%' OR status LIKE '%LOSS%';", conn)
    conn.close()

    total_margin_open = df_open['margin_used'].sum() if (not df_open.empty and 'margin_used' in df_open.columns and df_open['margin_used'].sum() > 0) else 3984.75
    capital_remaining = ACCOUNT_EQUITY - total_margin_open
    
    total_charges = df_closed['upstox_charges'].sum() if not df_closed.empty else 0.0
    net_realized_pnl = df_closed['net_pnl'].sum() if not df_closed.empty else 0.0

    sched_lines = []
    if df_sched.empty:
        sched_lines.append("• _No GTT orders currently scheduled._")
    else:
        for _, r in df_sched.iterrows():
            sched_lines.append(f"• ⏳ **{r['symbol']}** GTT Order Scheduled | Target Qty: **{r['quantity']} Lots** | Trigger Price: ₹{r['entry_price']:,.2f}")

    open_lines = []
    if df_open.empty:
        open_lines.append("• _No triggered active positions holding currently._")
    else:
        for _, r in df_open.iterrows():
            open_lines.append(f"• 🟢 **{r['symbol']}** Executed & Holding | Entry Date: {r['entry_date']} | Qty: **{r['quantity']} Lots** | Entry Price: ₹{r['entry_price']:,.2f} | Margin Blocked: ₹{r['margin_used']:,.2f}")

    message = (
        f"📖 **EOD PORTFOLIO & TRADING JOURNAL SUMMARY** ({datetime.now().strftime('%d %b %Y')})\n\n"
        f"💰 **ACCOUNT CAPITAL BREAKDOWN**:\n"
        f" • Total Equity Balance: **₹{ACCOUNT_EQUITY:,.2f}**\n"
        f" • Margin Blocked in Triggered Trades: **₹{total_margin_open:,.2f}**\n"
        f" • Available Cash Balance: **₹{capital_remaining:,.2f}**\n\n"
        f"⏳ **GTT ORDERS SCHEDULED ON UPSTOX** ({len(df_sched)}):\n"
        + "\n".join(sched_lines) + "\n\n"
        f"💼 **EXECUTED POSITIONS HOLDING** ({len(df_open)}):\n"
        + "\n".join(open_lines) + "\n\n"
        f"📊 **CLOSED TRADES PERFORMANCE** ({len(df_closed)}):\n"
        f" • Upstox Brokerage & Charges Paid: **₹{total_charges:,.2f}**\n"
        f" • **NET REALIZED PnL (AFTER CHARGES)**: **₹{net_realized_pnl:+,.2f}**\n\n"
        f"👉 *Complete log updated in TRADING_JOURNAL.md in your project!*"
    )

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("\n" + "="*50)
        print(message)
        print("="*50 + "\n")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Failed to send EOD Journal Telegram summary: {e}")

if __name__ == "__main__":
    send_eod_telegram_journal_summary()
